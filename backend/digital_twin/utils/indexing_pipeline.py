from collections.abc import Callable
from functools import partial
from itertools import chain
from multiprocessing import Pool
from typing import List, Optional
from langchain.embeddings.base import Embeddings

from digital_twin.connectors.model import Document
from digital_twin.vectordb.chunking.chunk import Chunker, DefaultChunker
from digital_twin.vectordb.chunking.models import EmbeddedIndexChunk
from digital_twin.vectordb.interface import VectorDB
from digital_twin.embedding.interface import get_default_embedding_model

from digital_twin.vectordb.qdrant.store import QdrantDatastore


""" 
# Multi-processing experiment
def _indexing_pipeline(
    chunker: Chunker,
    embedder: Embedder,
    datastore: VectorDB,
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

def _indexing_pipeline(
    chunker: Chunker,
    embedder: Embeddings,
    datastore: VectorDB,
    documents: list[Document],
    user_id: str | None,
) -> list[EmbeddedIndexChunk]:
    # TODO: make entire indexing pipeline async to not block the entire process
    # when running on async endpoints
    chunks = list(chain(*[chunker.chunk(document) for document in documents]))
    chunks_with_embeddings = embedder.embed_documents([chunk.content for chunk in chunks])
    datastore.index(chunks_with_embeddings, user_id)
    return chunks_with_embeddings

def build_indexing_pipeline(
    *,
    chunker: Optional[Chunker] = None,
    embedder: Optional[Embeddings] = None,
    datastore: Optional[VectorDB] = None,
) -> Callable[[List[Document]], List[EmbeddedIndexChunk]]:
    """Builds a pipline which takes in a list of docs and indexes them.

    Default uses _ chunker, _ embedder, and qdrant for the datastore"""
    if chunker is None:
        chunker = DefaultChunker()

    if embedder is None:
        embedder = get_default_embedding_model()

    if datastore is None:
        datastore = QdrantDatastore()

    return partial(_indexing_pipeline, chunker, embedder, datastore)
