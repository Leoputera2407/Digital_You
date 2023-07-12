import json
from typing import Any, Generator
from bs4 import BeautifulSoup

from digital_twin.config.constants import DocumentSource, HTML_SEPARATOR
from digital_twin.config.app_config import INDEX_BATCH_SIZE
from digital_twin.connectors.interfaces import (
    GenerateDocumentsOutput, 
    LoadConnector,
    PollConnector,
    SecondsSinceUnixEpoch,
)
from digital_twin.connectors.notion.connector_parser import NotionParser
from digital_twin.connectors.notion.connector_auth import DB_CREDENTIALS_DICT_KEY

from digital_twin.connectors.model import Document, Section
from digital_twin.utils.logging import setup_logger


logger = setup_logger()

from datetime import datetime, timezone

def parse_html(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")

    # Extract specific sections of the HTML if available
    sections = ["sidebar", "header", "footer", "nav"]
    for section in sections:
        for tag in soup.find_all(True, {"class": lambda x: x and section in x.split()}):
            tag.extract()

    # Extract additional undesired tags
    undesired_tags = ["meta", "script", "style"]
    for tag in soup.find_all(undesired_tags):
        tag.extract()

    # Extract all the text
    page_text = soup.get_text(HTML_SEPARATOR)

    return page_text

def to_timestamp(date_str: str) -> SecondsSinceUnixEpoch:
    """
    Convert an ISO 8601 date-time string to a timestamp.
    """
    # Convert the ISO 8601 date-time string to a datetime object.
    datetime_obj = datetime.fromisoformat(date_str)

    # Convert the datetime object to a timestamp.
    timestamp = datetime_obj.replace(tzinfo=timezone.utc).timestamp()

    return timestamp

def fetch_notion_pages(
    parser: NotionParser,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> list[dict[str, Any]]:
    if time_range_start is not None or time_range_end is not None:
        pages = []
        request_body = {
            "page_size": 20, # We'll pull the latest 20 pages at a time
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time",
            }
        }
        while True:
            batch, next_cursor = parser.notion_search(request_body)
            if not batch:
                break
            for page in batch:
                last_edited_time = to_timestamp(page["last_edited_time"])
                if time_range_start is not None and last_edited_time < time_range_start:
                    return pages
                if time_range_end is not None and last_edited_time > time_range_end:
                    continue
                pages.append(page)

            if not next_cursor:
                break
            request_body["start_cursor"] = next_cursor

        return pages
    else:
        # Full load, if no date range specified
        all_pages, next_cursor = parser.notion_search({})
        while next_cursor:
            new_pages, next_cursor = parser.notion_search({"start_cursor": next_cursor})
            all_pages.extend(new_pages)
        return all_pages

def get_notion_pages_in_batches(
    pages: list[dict[str, Any]], 
    batch_size: int
) -> Generator[list[dict[str, Any]], None, None]:
    for i in range(0, len(pages), batch_size):
        yield pages[i: i + batch_size]

class NotionConnector(LoadConnector, PollConnector):
    def __init__(self, workspace: str, batch_size: int = INDEX_BATCH_SIZE) -> None:
        self.batch_size = batch_size
        self.workspace = workspace
        self.access_token: str | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.access_token = credentials.get(DB_CREDENTIALS_DICT_KEY)
        return None
    
    def _fetch_docs_from_notion(
        self,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        if self.access_token is None:
            raise PermissionError("Not logged into Notion")

        parser = NotionParser(self.access_token)
        all_pages = fetch_notion_pages(parser, time_range_start, time_range_end)

        for page_batch in get_notion_pages_in_batches(all_pages, self.batch_size):
            batch: list(Document) = []
            for item in page_batch:
                object_type = item.get('object')
                object_id = item.get('id')
                url = item.get('url')

                if object_type == 'page':
                    blocks = parser.notion_get_blocks(object_id)
                    html = parser.parse_notion_blocks(blocks)
                    properties_metadata = parser.parse_desired_metadata_dict(item)

                    html = f"<div>{html}</div>"
                    batch.append(Document(
                        id=url,
                        sections=[
                            Section(
                                link=url, 
                                text=parse_html(html)
                            )
                        ],
                        source=DocumentSource.NOTION,
                        semantic_identifier=properties_metadata["title"],
                        metadata={
                            "updated_at": properties_metadata["last_edited_time"],
                            "title": properties_metadata["title"],
                            "created_at": properties_metadata["created_time"],
                            "created_by": properties_metadata["created_by"],
                            "last_edited_by": properties_metadata["last_edited_by"],
                        },
                    )
                    )
            yield batch

    def load_from_state(self) -> GenerateDocumentsOutput:
        yield from self._fetch_docs_from_notion()

    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        yield from self._fetch_docs_from_notion(start, end)
