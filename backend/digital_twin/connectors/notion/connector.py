import json
from typing import Any, Generator

from digital_twin.config.constants import DocumentSource
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

def to_timestamp(date_str: str) -> SecondsSinceUnixEpoch:
    """
    Convert an ISO 8601 date-time string to a timestamp.
    """
    # Convert the ISO 8601 date-time string to a datetime object.
    datetime_obj = datetime.fromisoformat(date_str)

    # Convert the datetime object to a timestamp.
    timestamp = datetime_obj.replace(tzinfo=timezone.utc).timestamp()

    return timestamp


def get_notion_pages_in_batches(
    pages: list[dict[str, Any]], 
    batch_size: int = INDEX_BATCH_SIZE,
    time_range_start: SecondsSinceUnixEpoch | None = None,
    time_range_end: SecondsSinceUnixEpoch | None = None,
) -> Generator[list[dict[str, Any]], None, None]:

    if time_range_start is not None:
        pages = [page for page in pages if to_timestamp(page['last_edited_time']) >= time_range_start]
    if time_range_end is not None:
        pages = [page for page in pages if to_timestamp(page['last_edited_time']) <= time_range_end]

    for i in range(0, len(pages), batch_size):
        yield pages[i: i + batch_size]


class NotionConnector(LoadConnector, PollConnector):
    def __init__(self, batch_size: int = INDEX_BATCH_SIZE) -> None:
        self.batch_size = batch_size
        self.access_token: str | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        access_token_json_str = credentials.get(DB_CREDENTIALS_DICT_KEY)
        if not access_token_json_str:
            raise ValueError("Access token not found in credentials")

        access_token_json = json.loads(access_token_json_str)
        self.access_token = access_token_json.get("access_token")
        return None
    
    def _fetch_docs_from_notion(
        self,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        if self.access_token is None:
            raise PermissionError("Not logged into Notion")

        parser = NotionParser(self.access_token)
        all_pages = parser.notion_search({})

        for page_batch in get_notion_pages_in_batches(all_pages, self.batch_size, time_range_start, time_range_end):
            batch: list(Document) = []
            for item in page_batch:
                object_type = item.get('object')
                object_id = item.get('id')
                url = item.get('url')
                title = ""

                if object_type == 'page':
                    title = parser.parse_title(item)
                    blocks = parser.notion_get_blocks(object_id)
                    html = parser.parse_notion_blocks(blocks)
                    properties_html = parser.parse_properties(item)
                    html = f"<div><h1>{title}</h1>{properties_html}{html}</div>"
                    batch.append(Document(
                        id=url,
                        sections=[
                            Section(
                                link=url, 
                                text=html
                            )
                        ],
                        source=DocumentSource.NOTION,
                        semantic_identifier=object_id,
                        metadata={
                            "last_modified": item["last_edited_time"],
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






