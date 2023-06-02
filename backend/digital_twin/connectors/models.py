from dataclasses import dataclass
from enum import Enum
from typing import Any


from digital_twin.config.constants import DocumentSource

# Sometimes a file could be split into multipe sections due to pagination
# This class handles that edge case
@dataclass
class Section:
    link: str | None
    text: str

# This is the class that will be partition on the TextSplitter/Chunker
@dataclass
class Document:
    id: str  # This must be unique or during indexing/reindexing, chunks will be overwritten
    sections: list[Section]
    source: DocumentSource
    semantic_identifier: str | None
    metadata: dict[str, Any] | None


def get_raw_document_text(document: Document) -> str:
    return "\n\n".join([section.text for section in document.sections])