from datetime import datetime
from typing import Union

import requests
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from digital_twin.connectors.interfaces import SecondsSinceUnixEpoch
from digital_twin.connectors.linear.model import Issue, Label, LinearOrganization, LinearTeam, Person


class LinearGraphQLClient:
    def __init__(self, linear_access_token: str):
        self.base_url = "https://api.linear.app/graphql"
        self.linear_token = linear_access_token
        self.headers = {"Authorization": f"Bearer {linear_access_token}"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(RequestException),
    )
    def execute_graphql_query(self, query: str, variables: dict | None = None):
        data: dict[str, Union[str, dict]] = {"query": query}
        if variables:
            data["variables"] = variables

        try:
            request = requests.post(self.base_url, json=data, headers=self.headers)
            if request.status_code == 200:
                return request.json()
            else:
                request.raise_for_status()
        except RequestException as e:
            print(f"Request failed: {e}")
            raise e

    def _raise_if_error_response(self, response: dict):
        if response.get("errors"):
            error_messages = []
            for error in response.get("errors", []):
                extensions = error.get("extensions", {})
                user_presentable_message = extensions.get("userPresentableMessage")
                if user_presentable_message:
                    error_messages.append(user_presentable_message)
                else:
                    error_messages.append(error.get("message", "Unknown error"))

            raise Exception("; ".join(error_messages))

    def get_issues_data(
        self,
        team_id: str,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> list[Issue]:
        query = """
            query ($team_id: String!, $after: String) {
                team(id: $team_id) {
                    issues(first: 100, after: $after, orderBy: updatedAt) {
                        nodes {
                            id
                            title
                            description
                            url
                            createdAt
                            updatedAt
                            archivedAt
                            assignee {
                                id
                                name
                                email
                            }
                            labels {
                                nodes {
                                    name
                                }
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
        """

        issues_data = []
        after = None
        while True:
            variables = {"team_id": team_id, "after": after}
            response = self.execute_graphql_query(query, variables)
            self._raise_if_error_response(response)
            for node in response.get("data", {}).get("team", {}).get("issues", {}).get("nodes", []):
                issue = node
                if issue.get("updatedAt") is None:
                    continue
                try:
                    last_modified = datetime.fromisoformat(issue["updatedAt"]).timestamp()
                except Exception:
                    last_modified = None

                if last_modified is not None:
                    if time_range_end is not None and last_modified > time_range_end:
                        continue

                    if time_range_start is not None and last_modified < time_range_start:
                        break

                assignee_data = issue.get("assignee", {})
                assignee = None
                if assignee_data:
                    assignee = Person(
                        id=assignee_data.get("id", ""),
                        name=assignee_data.get("name", ""),
                        email=assignee_data.get("email", ""),
                    )

                issue_data = Issue(
                    id=issue.get("id", ""),
                    title=issue.get("title", ""),
                    description=issue.get("description") or "",
                    url=issue.get("url", ""),
                    created_at=datetime.fromisoformat(issue.get("createdAt", "")).timestamp()
                    if issue.get("createdAt")
                    else None,
                    updated_at=datetime.fromisoformat(issue.get("updatedAt", "")).timestamp()
                    if issue.get("updatedAt")
                    else None,
                    archived_at=datetime.fromisoformat(issue.get("archivedAt", "")).timestamp()
                    if issue.get("archivedAt")
                    else None,
                    assignee=assignee,
                    labels=[Label(name=l.get("name", "")) for l in issue.get("labels", {}).get("nodes", [])]
                    if issue.get("labels")
                    else [],
                )
                issues_data.append(issue_data)

            if not response.get("data", {}).get("team", {}).get("issues", {}).get("pageInfo", {}).get(
                "hasNextPage", False
            ) or (
                time_range_start is not None
                and last_modified is not None
                and last_modified < time_range_start
            ):
                break

            after = (
                response.get("data", {})
                .get("team", {})
                .get("issues", {})
                .get("pageInfo", {})
                .get("endCursor", None)
            )

        return issues_data

    def get_user_organization_and_teams(self) -> LinearOrganization:
        """
        Returns the organization and teams of the user
        """
        query = """
                query {
                    viewer {
                        organization {
                            id
                            name
                            teams(first: 100) { 
                                nodes {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            """
        response = self.execute_graphql_query(query)
        self._raise_if_error_response(response)
        data = response.get("data", {}).get("viewer", {}).get("organization", {})

        if not data:
            raise ValueError("No organization data found")

        org_id = data.get("id")
        org_name = data.get("name")
        team_nodes = data.get("teams", {}).get("nodes", [])

        teams = []
        for team_node in team_nodes:
            team = LinearTeam(id=team_node.get("id"), name=team_node.get("name"))
            teams.append(team)

        organization = LinearOrganization(id=org_id, name=org_name, teams=teams)
        return organization

    def get_auth_user(self):
        query = """
            query {
                viewer {
                    id
                    name
                    email
                }
            }
        """
        response = self.execute_graphql_query(query)
        viewer = response.get("data", {}).get("viewer", {})
        self._raise_if_error_response(response)
        return Person(
            id=viewer.get("id", ""),
            name=viewer.get("name", ""),
            email=viewer.get("email", ""),
        )
