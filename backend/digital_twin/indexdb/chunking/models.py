import inspect
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from digital_twin.config.constants import BLURB, METADATA, SEMANTIC_IDENTIFIER, SOURCE_LINKS
from digital_twin.connectors.model import Document
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


class IndexType(Enum):
    QDRANT = "qdrant"
    TYPESENSE = "typesense"


@dataclass
class BaseChunk:
    chunk_id: int
    blurb: str  # The first sentence(s) of the first Section of the chunk
    content: str
    source_links: dict[int, str] | None  # Holds the link and the offsets into the raw Chunk text
    # True if this Chunk's start is not at the start of a Section
    section_continuation: bool


@dataclass
class IndexChunk(BaseChunk):
    source_document: Document


@dataclass
class EmbeddedIndexChunk(IndexChunk):
    embeddings: list[list[float]]


@dataclass
class InferenceChunk(BaseChunk):
    document_id: str
    source_type: str
    semantic_identifier: str
    metadata: dict[str, Any]
    score_info: dict[str, Any]
    index_type: IndexType

    @classmethod
    def from_dict(
        cls,
        init_dict: dict[str, Any],
        score_info: dict[str, Any],
        index_type: str,
    ) -> "InferenceChunk":
        init_kwargs = {k: v for k, v in init_dict.items() if k in inspect.signature(cls).parameters}
        if SOURCE_LINKS in init_kwargs:
            source_links = init_kwargs[SOURCE_LINKS]
            source_links_dict = json.loads(source_links) if isinstance(source_links, str) else source_links
            init_kwargs[SOURCE_LINKS] = {
                int(k): v for k, v in cast(dict[str, str], source_links_dict).items()
            }
        from digital_twin.utils.logging import setup_logger

        if METADATA in init_kwargs:
            init_kwargs[METADATA] = json.loads(init_kwargs[METADATA])
        else:
            init_kwargs[METADATA] = {}
        if init_kwargs.get(SEMANTIC_IDENTIFIER) is None:
            logger.error(
                f"Chunk with blurb: {init_kwargs.get(BLURB, 'Unknown')[:50]}... has no Semantic Identifier"
            )

        init_kwargs["score_info"] = score_info
        init_kwargs["index_type"] = index_type
        return cls(**init_kwargs)
