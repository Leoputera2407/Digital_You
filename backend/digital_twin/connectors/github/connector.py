import itertools
from typing import Any
from collections.abc import Generator

from github import Github
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest

from digital_twin.config.app_config import (
    GITHUB_ACCESS_TOKEN,
    INDEX_BATCH_SIZE,
)

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.interfaces import LoadConnector, GenerateDocumentsOutput
from digital_twin.connectors.model import Document, Section
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

github_client = Github(GITHUB_ACCESS_TOKEN)


def get_pr_batches(
    pull_requests: PaginatedList, batch_size: int
) -> Generator[list[PullRequest], None, None]:
    it = iter(pull_requests)
    while True:
        batch = list(itertools.islice(it, batch_size))
        if not batch:
            break
        yield batch


class GithubConnector(LoadConnector):
    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        batch_size: int = INDEX_BATCH_SIZE,
        state_filter: str = "all",
    ) -> None:
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.batch_size = batch_size
        self.state_filter = state_filter
        self.github_client: Github | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.github_client = Github(credentials["github_access_token"])
        return None

    def load_from_state(self) -> GenerateDocumentsOutput:
        if self.github_client is None:
            raise PermissionError(
                "Github Client is not set up, was load_credentials called?"
            )
        repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
        pull_requests = repo.get_pulls(state=self.state_filter)
        for pr_batch in get_pr_batches(pull_requests, self.batch_size):
            doc_batch = []
            for pull_request in pr_batch:
                full_context = f"Pull-Request {pull_request.title}  {pull_request.body}"
                doc_batch.append(
                    Document(
                        id=pull_request.html_url,
                        sections=[
                            Section(link=pull_request.html_url, text=full_context)
                        ],
                        source=DocumentSource.GITHUB,
                        semantic_identifier=pull_request.title,
                        metadata={
                            "last_modified": pull_request.last_modified,
                            "merged": pull_request.merged,
                            "state": pull_request.state,
                        },
                    )
                )

            yield doc_batch
