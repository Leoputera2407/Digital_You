import requests
from typing import List
from datetime import datetime
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from digital_twin.connectors.linear.model import (
    Issue, 
    Person, 
    Label,
    LinearOrganization,
    LinearTeam,
)
from digital_twin.connectors.interfaces import SecondsSinceUnixEpoch



class LinearGraphQLClient:
    def __init__(self, linear_access_token: str):
        self.base_url = 'https://api.linear.app/graphql'
        self.linear_token = linear_access_token
        self.headers = {"Authorization": f"Bearer {linear_access_token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(RequestException))
    def execute_graphql_query(self, query: str, variables: dict = None):
        data = {'query': query}
        if variables:
            data['variables'] = variables

        try:
            request = requests.post(self.base_url, json=data, headers=self.headers)
            if request.status_code == 200:
                return request.json()
            else:
                request.raise_for_status()
        except RequestException as e:
            print(f"Request failed: {e}")
            raise e

    def get_issues_data(
            self, 
            team_id: str, 
            time_range_start: SecondsSinceUnixEpoch | None = None, 
            time_range_end: SecondsSinceUnixEpoch | None = None
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
            variables = {
                "team_id": team_id, 
                "after": after
            }
            response = self.execute_graphql_query(query, variables)

            for node in response['data']['team']['issues']['nodes']:
                issue = node
                if issue['updatedAt'] is None:
                    continue
                last_modified = datetime.fromisoformat(issue['updatedAt']).timestamp()

                if time_range_start is not None and last_modified < time_range_start:
                    break
                if time_range_end is not None and last_modified > time_range_end:
                    continue

                issue_data = Issue(
                    id=issue["id"],
                    title=issue["title"],
                    description=issue["description"] if issue["description"] else "",
                    url=issue["url"],
                    created_at=datetime.fromisoformat(issue["createdAt"]).timestamp() if issue["createdAt"] else None,
                    updated_at=datetime.fromisoformat(issue["updatedAt"]).timestamp() if issue["updatedAt"] else None,
                    archived_at=datetime.fromisoformat(issue["archivedAt"]).timestamp() if issue["archivedAt"] else None,
                    assignee=Person(id=issue["assignee"]["id"], name=issue["assignee"]["name"], email=issue["assignee"]["email"]) if issue["assignee"] else None,
                    labels=[Label(name=l["name"]) for l in issue["labels"]["nodes"]],
                )
                issues_data.append(issue_data)

            if not response['data']['team']['issues']['pageInfo']['hasNextPage'] or (time_range_start is not None and last_modified < time_range_start):
                break

            after = response['data']['team']['issues']['pageInfo']['endCursor']

        return issues_data

    def get_user_organization_and_teams(self) -> LinearOrganization:
        """
        Returns the organization and teams of the user
        -- For now, we assume all org only has 1 team
        """
        query = """
                query {
                    viewer {
                        teams(first: 100) { 
                            nodes {
                                id
                                name
                                organization {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            """
        response = self.execute_graphql_query(query)
        teams = []
        org_node = None

      

        for team_node in response['data']['viewer']['teams']['nodes']:
            if org_node is None:
                org_node = team_node['organization']
                
            team = LinearTeam(id=team_node['id'], name=team_node['name'])
            teams.append(team)

        organization = LinearOrganization(id=org_node['id'], name=org_node['name'], teams=teams)

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

        return Person(
            id=response['data']['viewer']['id'], 
            name=response['data']['viewer']['name'],
            email=response['data']['viewer']['email']
        )
