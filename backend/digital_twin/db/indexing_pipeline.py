from collections.abc import Callable
from functools import partial
from itertools import chain
from typing import List, Optional, Protocol
from uuid import UUID

from digital_twin.config.app_config import (
    TYPESENSE_DEFAULT_COLLECTION,
    QDRANT_DEFAULT_COLLECTION,
)
from digital_twin.connectors.model import Document
from digital_twin.indexdb.chunking.chunk import Chunker, DefaultChunker
from digital_twin.indexdb.chunking.models import EmbeddedIndexChunk
from digital_twin.indexdb.interface import VectorIndexDB, KeywordIndex
from digital_twin.indexdb.qdrant.store import QdrantVectorDB
from digital_twin.indexdb.typesense.store import TypesenseIndex
from digital_twin.search.interface import DefaultEmbedder
from digital_twin.search.models import Embedder
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


class IndexingPipelineProtocol(Protocol):
    def __call__(
        self, documents: list[Document], user_id: UUID | None
    ) -> tuple[int, int]:        
        ...

def _indexing_pipeline(
    chunker: Chunker,
    embedder: Embedder,
    vectordb: VectorIndexDB,
    keyword_index: KeywordIndex,
    documents: list[Document],
    user_id: str | None,
) -> int:
    """Takes different pieces of the indexing pipeline and applies it to a batch of documents
    Note that the documents should already be batched at this point so that it does not inflate the
    memory requirements"""
    # TODO: make entire indexing pipeline async to not block the entire process
    # when running on async endpoints
    chunks = list(chain(*[chunker.chunk(document) for document in documents]))
    net_doc_count_keyword = keyword_index.index(chunks, user_id)
    chunks_with_embeddings = embedder.embed(chunks)
    net_doc_count_vector = vectordb.index(chunks_with_embeddings, user_id)
    if net_doc_count_vector != net_doc_count_vector:
        logger.exception(
            "Number of documents indexed by keyword and vector indices aren't align"
        )
    net_new_docs = max(net_doc_count_keyword, net_doc_count_vector)
    logger.info(f"Indexed {net_new_docs} new documents")
    return net_new_docs, len(chunks)

def build_indexing_pipeline(
    *,
    chunker: Optional[Chunker] = None,
    embedder: Optional[Embedder] = None,
    vectordb: Optional[VectorIndexDB] = None,
    keyword_index: Optional[KeywordIndex] = None,
) -> Callable[[List[Document]], List[EmbeddedIndexChunk]]:
    """Builds a pipline which takes in a list of docs and indexes them.

    Default uses _ chunker, _ embedder, and qdrant for the datastore"""
    if chunker is None:
        chunker = DefaultChunker()

    if embedder is None:
        embedder = DefaultEmbedder()
    
    if keyword_index is None:
        keyword_index = TypesenseIndex(collection=TYPESENSE_DEFAULT_COLLECTION)

    if vectordb is None:
        vectordb = QdrantVectorDB(collection=QDRANT_DEFAULT_COLLECTION)

    return partial(
        _indexing_pipeline, 
        chunker=chunker, 
        embedder=embedder,
        vectordb=vectordb,
        keyword_index=keyword_index,
    )
