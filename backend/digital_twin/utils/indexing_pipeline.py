from collections.abc import Callable
from functools import partial
from itertools import chain
from multiprocessing import Pool
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


""" 
# Multi-processing experiment
def _indexing_pipeline(
    chunker: Chunker,
    embedder: Embedder,
    datastore: VectorIndexDB,
    documents: List[Document],
) -> List[EmbeddedIndexChunk]:
    # TODO: Not sure if this is CPU-bound or IO-bound operation
    # For now, use multiprocessing and assume it's CPU-bound
    with Pool() as pool:
        chunks = List(chain(*pool.map(chunker.chunk, documents)))
        chunks_with_embeddings = List(pool.map(embedder.embed, chunks))
        pool.map(datastore.index, chunks_with_embeddings)

    return chunks_with_embeddings
 """

class IndexingPipelineProtocol(Protocol):
    def __call__(self, documents: list[Document], user_id: UUID | None) -> int:
        ...

def _indexing_pipeline(
    chunker: Chunker,
    embedder: Embedder,
    datastore: VectorIndexDB,
    keyword_index: KeywordIndex,
    documents: list[Document],
    user_id: str | None,
) -> int:
    # TODO: make entire indexing pipeline async to not block the entire process
    # when running on async endpoints
    chunks = list(chain(*[chunker.chunk(document) for document in documents]))
    chunks_with_embeddings = embedder.embed(chunks)
    net_doc_count_keyword = keyword_index.index(chunks, user_id)
    net_doc_count_vector = datastore.index(chunks_with_embeddings, user_id)
    if net_doc_count_vector != net_doc_count_vector:
        logger.exception(
            "Number of documents indexed by keyword and vector indices aren't align"
        )
    return max(net_doc_count_vector, net_doc_count_keyword)

def build_indexing_pipeline(
    *,
    chunker: Optional[Chunker] = None,
    embedder: Optional[Embedder] = None,
    datastore: Optional[VectorIndexDB] = None,
    keyword_index: Optional[KeywordIndex] = None,
    typesense_collection_name: Optional[str] = None,
    qdrant_collection_name: Optional[str] = None,
) -> Callable[[List[Document]], List[EmbeddedIndexChunk]]:
    """Builds a pipline which takes in a list of docs and indexes them.

    Default uses _ chunker, _ embedder, and qdrant for the datastore"""
    if chunker is None:
        chunker = DefaultChunker()

    if embedder is None:
        embedder = DefaultEmbedder()
    
    if keyword_index is None:
        keyword_index = TypesenseIndex(typesense_collection_name if typesense_collection_name else TYPESENSE_DEFAULT_COLLECTION)

    if datastore is None:
        datastore = QdrantVectorDB(qdrant_collection_name if qdrant_collection_name else QDRANT_DEFAULT_COLLECTION)

    return partial(_indexing_pipeline, chunker, embedder, datastore)
