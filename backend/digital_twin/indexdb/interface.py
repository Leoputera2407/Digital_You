import abc
from typing import Generic
from typing import TypeVar
from uuid import UUID

from digital_twin.indexdb.chunking.models import (
    BaseChunk,
    EmbeddedIndexChunk,
    IndexChunk,
    InferenceChunk,
)


T = TypeVar("T", bound=BaseChunk)
IndexDBFilter = dict[str, str | list[str] | None]


class DocumentIndex(Generic[T], abc.ABC):
    @abc.abstractmethod
    def index(self, chunks: list[T], user_id: UUID | None) -> int:
        """Indexes document chunks into the Document Index and return the number of new documents"""
        raise NotImplementedError


class VectorIndexDB(DocumentIndex[EmbeddedIndexChunk], abc.ABC):
    @abc.abstractmethod
    def semantic_retrieval(
        self,
        query: str,
        user_id: UUID | None,
        filters: list[IndexDBFilter] | None,
        num_to_retrieve: int,
    ) -> list[InferenceChunk]:
        raise NotImplementedError


class KeywordIndex(DocumentIndex[IndexChunk], abc.ABC):
    @abc.abstractmethod
    def keyword_search(
        self,
        query: str,
        user_id: UUID | None,
        filters: list[IndexDBFilter] | None,
        num_to_retrieve: int,
    ) -> list[InferenceChunk]:
        raise NotImplementedError
