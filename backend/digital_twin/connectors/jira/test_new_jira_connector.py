from datetime import datetime
from typing import Any, List, Optional, Tuple

from digital_twin.config.app_config import INDEX_BATCH_SIZE
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.interfaces import (
    GenerateDocumentsOutput,
    LoadConnector,
    PollConnector,
    SecondsSinceUnixEpoch,
)
from digital_twin.connectors.jira.test_jira_client import JiraClient
from digital_twin.connectors.model import Document, Section


class JiraConnector(LoadConnector, PollConnector):
    def __init__(
        self,
        jira_domain: str,
        jira_project: str,
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.jira_domain = jira_domain
        self.jira_project = jira_project
        self.batch_size = batch_size
        self.jira_client: Optional[JiraClient] = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        user_email = credentials["jira_user_email"]
        api_token = credentials["jira_api_token"]
        jira_domain = credentials["jira_domain"]
        self.jira_client = JiraClient(self.jira_domain, api_token, user_email)
        return None

    def fetch_jira_issues_batch(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch, startAt: int = 0
    ) -> Tuple[List[Document], int]:
        if self.jira_client is None:
            raise PermissionError("Jira Client is not set up, was load_credentials called?")

        issues = self.jira_client.get_issues_and_comments(
            self.jira_project, start, end, startAt=startAt, maxResults=self.batch_size
        )

        doc_batch = []
        for issue in issues["issues"]:
            semantic_rep = (
                f"Jira Ticket Summary: {issue['fields']['summary']}\n"
                f"Description: {issue['fields']['description']}\n"
                + "\n".join(
                    [f"Comment: {comment['body']}" for comment in issue["fields"]["comment"]["comments"]]
                )
            )

            page_url = f"https://{self.jira_client.get_domain()}/browse/{issue['key']}"

            doc_batch.append(
                Document(
                    id=page_url,
                    sections=[Section(link=page_url, text=semantic_rep)],
                    source=DocumentSource.JIRA,
                    semantic_identifier=issue["fields"]["summary"],
                    metadata={},
                )
            )
        return doc_batch, len(issues["issues"])

    def load_from_state(self) -> GenerateDocumentsOutput:
        if self.jira_client is None:
            raise PermissionError("Jira Client is not set up, was load_credentials called?")

        start_ind = 0
        while True:
            doc_batch, fetched_batch_size = self.fetch_jira_issues_batch(
                0, int(datetime.now().timestamp()), startAt=start_ind
            )

            if doc_batch:
                yield doc_batch

            start_ind += fetched_batch_size
            if fetched_batch_size < self.batch_size:
                break

    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        if self.jira_client is None:
            raise PermissionError("Jira Client is not set up, was load_credentials called?")

        start_ind = 0
        while True:
            doc_batch, fetched_batch_size = self.fetch_jira_issues_batch(start, end, startAt=start_ind)

            if doc_batch:
                yield doc_batch

            start_ind += fetched_batch_size
            if fetched_batch_size < self.batch_size:
                break
