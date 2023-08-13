import abc
import datetime
from collections.abc import Generator
from typing import Any

from digital_twin.connectors.model import Document

SecondsSinceUnixEpoch = float

GenerateDocumentsOutput = Generator[list[Document], None, None]


class BaseConnector(abc.ABC):
    @abc.abstractmethod
    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    @staticmethod
    def parse_metadata(metadata: dict[str, Any]) -> list[str]:
        """Parse the metadata for a document/chunk into a string to pass to Generative AI as additional context"""
        custom_parser_req_msg = "Specific metadata parsing required, connector has not implemented it."
        metadata_lines = []
        for metadata_key, metadata_value in metadata.items():
            if isinstance(metadata_value, str):
                metadata_lines.append(f"{metadata_key}: {metadata_value}")
            elif isinstance(metadata_value, (int, float)):
                metadata_lines.append(f"{metadata_key}: {str(metadata_value)}")
            elif isinstance(metadata_value, datetime.datetime):
                # Convert datetime objects to their string representation
                metadata_lines.append(f"{metadata_key}: {metadata_value.strftime('%Y-%m-%d %H:%M:%S')}")
            elif isinstance(metadata_value, bool):
                metadata_lines.append(f"{metadata_key}: {'True' if metadata_value else 'False'}")
            elif isinstance(metadata_value, list):
                # Convert each item in the list to its string representation
                str_values = []
                for val in metadata_value:
                    if isinstance(val, datetime.datetime):  # Check if it's a datetime object
                        str_values.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                    elif isinstance(val, (str, int, float)):
                        str_values.append(str(val))  # Convert other types (int, float, etc.) to str
                    elif isinstance(val, bool):
                        str_values.append("True" if val else "False")
                    else:
                        # Unsupported type continue
                        continue
                metadata_lines.append(f'{metadata_key}: {", ".join(str_values)}')
            else:
                continue
                # raise RuntimeError(custom_parser_req_msg)
        return metadata_lines


# Large set update or reindex, generally pulling a complete state or from a savestate file
class LoadConnector(BaseConnector):
    @abc.abstractmethod
    def load_from_state(self) -> GenerateDocumentsOutput:
        raise NotImplementedError


# Small set updates by time
class PollConnector(BaseConnector):
    @abc.abstractmethod
    def poll_source(
        self, start: SecondsSinceUnixEpoch, end: SecondsSinceUnixEpoch
    ) -> GenerateDocumentsOutput:
        raise NotImplementedError


# Event driven
class EventConnector(BaseConnector):
    @abc.abstractmethod
    def handle_event(self, event: Any) -> GenerateDocumentsOutput:
        raise NotImplementedError
