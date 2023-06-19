import time
from collections.abc import Generator
from typing import Any, Type

from digital_twin.config.constants import DocumentSource
from digital_twin.connectors.github.connector import GithubConnector
from digital_twin.connectors.google_drive.connector import GoogleDriveConnector
from digital_twin.connectors.slack.connector import SlackLoadConnector, SlackPollConnector
from digital_twin.connectors.web.connector import WebConnector
from digital_twin.connectors.confluence.connector import ConfluenceConnector
from digital_twin.connectors.adhoc_upload.connector import AdhocUploadConnector
from digital_twin.connectors.notion.connector import NotionConnector


from digital_twin.connectors.interfaces import (
    BaseConnector,
    EventConnector,
    LoadConnector,
    PollConnector,
)
from digital_twin.connectors.model import Document, InputType

_NUM_SECONDS_IN_DAY = 86400


class ConnectorMissingException(Exception):
    pass


"""
DocumentSource.WEB: WebConnector,
DocumentSource.ADHOC_UPLOAD: AdhocUploadConnector,
DocumentSource.SLACK: {
    InputType.LOAD_STATE: SlackLoadConnector,
    InputType.POLL: SlackPollConnector,
},
"""

def identify_connector_class(
    source: DocumentSource,
    input_type: InputType,
) -> Type[BaseConnector]:
    connector_map = {
        DocumentSource.GITHUB: GithubConnector,
        DocumentSource.GOOGLE_DRIVE: GoogleDriveConnector,
        DocumentSource.CONFLUENCE: ConfluenceConnector,
        DocumentSource.NOTION: NotionConnector,
    }
    connector_by_source = connector_map.get(source, {})

    if isinstance(connector_by_source, dict):
        connector = connector_by_source.get(input_type)
    else:
        connector = connector_by_source

    if connector is None:
        raise ConnectorMissingException(f"Connector not found for source={source}")

    if any(
        [
            input_type == InputType.LOAD_STATE
            and not issubclass(connector, LoadConnector),
            input_type == InputType.POLL and not issubclass(connector, PollConnector),
            input_type == InputType.EVENT and not issubclass(connector, EventConnector),
        ]
    ):
        raise ConnectorMissingException(
            f"Connector for source={source} does not accept input_type={input_type}"
        )

    return connector


def instantiate_connector(
    source: DocumentSource,
    input_type: InputType,
    connector_specific_config: dict[str, Any],
    credentials: dict[str, Any],
) -> tuple[BaseConnector, dict[str, Any] | None]:
    connector_class = identify_connector_class(source, input_type)
    connector = connector_class(**connector_specific_config)
    new_credentials = connector.load_credentials(credentials)

    return connector, new_credentials
