from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel

from digital_twin.config.constants import DocumentSource

@dataclass
class Section:
    link: str
    text: str

@dataclass
class Document:
    id: str  # This must be unique or during indexing/reindexing, chunks will be overwritten
    sections: list[Section]
    source: DocumentSource
    semantic_identifier: str | None
    metadata: dict[str, Any] | None


def get_raw_document_text(document: Document) -> str:
    return "\n\n".join([section.text for section in document.sections])


class InputType(str, Enum):
    # e.g. loading a current full state or a save state, such as from a file
    LOAD_STATE = "load_state"
    # e.g. calling an API to get all documents in the last hour
    POLL = "poll"
    # e.g. registered an endpoint as a listener, and processing connector events
    EVENT = "event"


class ConnectorDescriptor(BaseModel):
    source: DocumentSource
    # how the raw data being indexed is procured
    input_type: InputType
    # what is passed into the __init__ of the connector described by `source`
    # and `input_type`
    connector_specific_config: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True
