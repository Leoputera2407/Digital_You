import requests
import base64
from datetime import datetime, timezone
from digital_twin.connectors.interfaces import SecondsSinceUnixEpoch

class JiraClient:
    def __init__(self, domain: str, api_key: str, user_name: str):
        self.domain = domain
        self.headers = {
            "Authorization": f'Basic {base64.b64encode(f"{user_name}:{api_key}".encode()).decode()}',
            "Accept": "application/json"
        }
        self.API_VERSION = "3"
        self.BASE_URL = f'https://{self.domain}/rest/api/{self.API_VERSION}'
    
    def get_domain(self) -> str:
        return self.domain
    
    def get_projects(self):
        response = requests.get(
            f'{self.BASE_URL}/project', 
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed with status code {response.status_code}")
            
    def get_issues_and_comments(self, project: str, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch, startAt: int = 0, maxResults: int = 50):
        start_date_str = datetime.fromtimestamp(start, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M"
        )
        end_date_str = datetime.fromtimestamp(end, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M"
        )

        jql = f"project={project} AND updated>='{start_date_str}' AND updated<='{end_date_str}'"
        
        response = requests.get(
            f'{self.BASE_URL}/search',
            headers=self.headers,
            params={
                'jql': jql,
                'startAt': startAt,
                'maxResults': maxResults,
                'fields': 'summary,description,comment',  # Request only necessary fields
            },
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed with status code {response.status_code}")
