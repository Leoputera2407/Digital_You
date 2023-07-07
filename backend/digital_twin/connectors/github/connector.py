import datetime
from typing import Any
from collections.abc import Generator

from github import Github
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile
from github.Repository import Repository

from digital_twin.config.app_config import INDEX_BATCH_SIZE
from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.interfaces import (
    LoadConnector, 
    PollConnector,
    GenerateDocumentsOutput,
    SecondsSinceUnixEpoch,
)
from digital_twin.connectors.model import Document, Section
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
DB_CREDENTIALS_DICT_KEY = "github_access_token"
MARKDOWN_EXT= (".md", ".rst", ".mdx", ".mkd", ".mdwn", ".mdown", ".mdtxt", ".mdtext", ".markdown")

def to_timestamp(date_str: str) -> SecondsSinceUnixEpoch:
    """
    Convert a RFC 1123 date-time string to a timestamp.
    """
    # Convert the RFC 1123 date-time string to a datetime object.
    datetime_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S GMT')

    # Convert the datetime object to a timestamp.
    timestamp = datetime.timestamp(datetime_obj)

    return timestamp


def get_markdown_and_code_contents(
    repo: Repository
) -> tuple[list[ContentFile], list[ContentFile]]:
    contents = repo.get_contents("")
    md_files = []
    code_files = []
    while len(contents) > 0:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        elif file_content.path.endswith(MARKDOWN_EXT):
            md_files.append(file_content)
        else:
            code_files.append(file_content)
    return md_files, code_files

def get_pr_batches(
    pull_requests: PaginatedList, 
    batch_size: int = INDEX_BATCH_SIZE,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Generator[list[PullRequest], None, None]:
    if time_range_start is not None:
        pull_requests = [pr for pr in pull_requests if to_timestamp(pr.last_modified) >= time_range_start]
    if time_range_end is not None:
        pull_requests = [pr for pr in pull_requests if to_timestamp(pr.last_modified) <= time_range_end]

    for i in range(0, len(pull_requests), batch_size):
        yield pull_requests[i: i + batch_size]

def get_markdown_text_in_batches(
    contents: list[ContentFile], 
    batch_size: int = INDEX_BATCH_SIZE,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Generator[list[ContentFile], None, None]:
    if time_range_start is not None:
        contents = [file for file in contents if to_timestamp(file.last_modified) >= time_range_start]
    if time_range_end is not None:
        contents = [file for file in contents if to_timestamp(file.last_modified) <= time_range_end]

    for i in range(0, len(contents), batch_size):
        yield contents[i: i + batch_size]

class GithubConnector(LoadConnector, PollConnector):
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
        self.github_client = Github(credentials[DB_CREDENTIALS_DICT_KEY])
        return None

    def _fetch_docs_from_github(
        self,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        if self.github_client is None:
            raise PermissionError(
                "Github Client is not set up, was load_credentials called?"
            )

        repo = self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
        pull_requests = repo.get_pulls(state=self.state_filter)

        for pr_batch in get_pr_batches(pull_requests, self.batch_size, time_range_start, time_range_end):
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

        # TODO: For now, we won't index the code files
        md_contents, _ = get_markdown_and_code_contents(repo)
        
        for content_batch in get_markdown_text_in_batches(md_contents, self.batch_size, time_range_start, time_range_end):
            doc_batch = []
            for content in content_batch:
                if content.path.lower().endswith(MARKDOWN_EXT):
                    doc_batch.append(
                        Document(
                            id=content.html_url,
                            sections=[
                                Section(
                                    link=content.html_url,
                                    text=content.decoded_content.decode("utf-8"),
                                )
                            ],
                            source=DocumentSource.GITHUB,
                            semantic_identifier=content.path,
                            metadata={
                                "last_modified": content.last_modified,
                                "path": content.path,
                                "type": content.type,
                            },
                        )
                    )
            yield doc_batch

    def load_from_state(self) -> GenerateDocumentsOutput:
        yield from self._fetch_docs_from_github()

    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        yield from self._fetch_docs_from_github(start, end)

