import requests
from datetime import datetime
from digital_twin.connectors.github.model import PullRequest, Person, Label


class GithubGraphQLClient:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {"Authorization": f"Bearer {github_token}"}

    @staticmethod
    def _map_state_filter(state_filter: str) -> list[str]:
        """
        Maps PyGithub pull request state filters to the corresponding GraphQL filters.
        
        Args:
            state_filter (str): The PyGithub pull request state filter.

        Returns:
            list[str]: The corresponding GraphQL pull request state filters.
        """
        state_map = {
            "all": ["OPEN", "CLOSED", "MERGED"],
            "open": ["OPEN"],
            "closed": ["CLOSED", "MERGED"],  # In GitHub API, 'closed' includes merged PRs
        }
        
        return state_map.get(state_filter.lower(), ["OPEN", "CLOSED", "MERGED"])
    
    def execute_graphql_query(self, query: str, variables: dict = None):
        data = {'query': query}
        if variables:
            data['variables'] = variables
            
        request = requests.post('https://api.github.com/graphql', json=data, headers=self.headers)
        
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception(f"Query failed with status code {request.status_code}. Query: {query}")
    
    def _raise_if_error_response(self, response: dict):
        if response.get('errors'):
            error_messages = []
            for error in response.get('errors', []):
                message = error.get('message', 'Unknown error')
                error_messages.append(message)
            raise Exception('; '.join(error_messages))
    
    def get_pull_request_data(
            self, 
            owner: str, 
            repo: str, 
            state_filter: str = 'all', 
            after: str = None, 
            time_range_start: float | None = None, 
            time_range_end: float | None = None
    ) -> list[PullRequest]:
        query = """
            query ($owner: String!, $repo: String!, $after: String, $state_filter: [PullRequestState!]) {
            repository(owner: $owner, name: $repo) {
                pullRequests(states: $state_filter, first: 100, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
                edges {
                    node {
                    title
                    body
                    html_url: url
                    number
                    createdAt
                    updatedAt
                    closedAt
                    mergedAt
                    merged
                    state
                    author {
                        login
                    }
                    reviews(first: 10) {
                        nodes {
                            author {
                                login
                            }
                        }
                    }
                    assignees(first: 10) {
                        nodes {
                        login
                        }
                    }
                    labels(first: 10) {
                        nodes {
                        name
                        }
                    }
                    comments(first: 1) {
                        totalCount
                    }
                    commits(first: 1) {
                        totalCount
                    }
                    }
                    cursor
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
                }
            }
            }
        """
        variables = {
            "owner": owner, 
            "repo": repo, 
            "state_filter": self._map_state_filter(state_filter), 
            "after": after
        }

        pull_requests_data = []
        while True:
            response = self.execute_graphql_query(query, variables)
            self._raise_if_error_response(response)
            for edge in response['data']['repository']['pullRequests']['edges']:
                pr = edge['node']
                if pr['updatedAt'] is None:
                    continue
                last_modified = datetime.fromisoformat(pr['updatedAt']).timestamp()

                if time_range_start is not None and last_modified < time_range_start:
                    break
                if time_range_end is not None and last_modified > time_range_end:
                    continue

                pr_data = PullRequest(
                    title=pr["title"],
                    body=pr["body"],
                    html_url=pr["html_url"],
                    number=pr["number"],
                    created_at=datetime.fromisoformat(pr["createdAt"]).timestamp() if pr["createdAt"] else None,
                    updated_at=datetime.fromisoformat(pr["updatedAt"]).timestamp() if pr["updatedAt"] else None,
                    closed_at=datetime.fromisoformat(pr["closedAt"]).timestamp() if pr["closedAt"] else None,
                    merged_at=datetime.fromisoformat(pr["mergedAt"]).timestamp() if pr["mergedAt"] else None,
                    merged=pr["merged"],
                    state=pr["state"],
                    author=Person(name=pr["author"]["login"]) if pr["author"] else None,
                    reviewers=[Person(name=r["author"]["login"]) for r in pr["reviews"]["nodes"] if r["author"]],
                    assignees=[Person(name=a["login"]) for a in pr["assignees"]["nodes"]],
                    labels=[Label(**l) for l in pr["labels"]["nodes"]],
                    comments=pr["comments"]["totalCount"],
                    commits=pr["commits"]["totalCount"],    
                )
                pull_requests_data.append(pr_data)

            if not response['data']['repository']['pullRequests']['pageInfo']['hasNextPage'] or (time_range_start is not None and last_modified < time_range_start):
                break

            variables['after'] = response['data']['repository']['pullRequests']['pageInfo']['endCursor']

        return pull_requests_data
