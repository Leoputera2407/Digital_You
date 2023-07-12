from typing import Any, Generator
from digital_twin.config.constants import DocumentSource, HTML_SEPARATOR
from digital_twin.connectors.linear. graphql import LinearGraphQLClient
from digital_twin.connectors.interfaces import (
    GenerateDocumentsOutput, 
    LoadConnector,
    PollConnector,
    SecondsSinceUnixEpoch,
)
from digital_twin.config.app_config import INDEX_BATCH_SIZE
from digital_twin.connectors.model import Document, Section
from digital_twin.connectors.linear.connector_auth import DB_CREDENTIALS_DICT_KEY
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

class LinearConnector(LoadConnector, PollConnector):
    def __init__(self, team_id: str, team_name: str, workspace: str, batch_size: int = INDEX_BATCH_SIZE) -> None:
        self.team_id = team_id
        self.team_name = team_name
        self.workspace = workspace
        self.batch_size = batch_size
        self.linear_client: LinearGraphQLClient | None = None

    
    def load_credentials(self, credentials: dict[str, Any]) -> None:
        self.linear_client = LinearGraphQLClient(credentials[DB_CREDENTIALS_DICT_KEY])
        return None
    
    def _fetch_issues_from_linear(
        self,
        team_id: str,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        if self.linear_client is None:
            raise ValueError("Linear client not initialized")
         
        all_issues = self.linear_client.get_issues_data(team_id, time_range_start, time_range_end)

        for i in range(0, len(all_issues), self.batch_size):
            batch: list[Document] = []
            for issue in all_issues[i: i + self.batch_size]:
                batch.append(Document(
                    id=issue.id,
                    sections=[
                        Section(
                            link=issue.url, 
                            text=issue.title + "\n" + issue.description
                        )
                    ],
                    source=DocumentSource.LINEAR,
                    semantic_identifier=issue.title,
                    metadata={
                        "created_at": issue.created_at,
                        "updated_at": issue.updated_at,
                        "archived_at": issue.archived_at,
                        "assignee": issue.assignee_names,
                        "labels": issue.label_names,
                    },
                )
                )
            yield batch

    def load_from_state(self) -> GenerateDocumentsOutput:     
        yield from self._fetch_issues_from_linear(self.team_id)

    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        yield from self._fetch_issues_from_linear(self.team_id, start, end)
