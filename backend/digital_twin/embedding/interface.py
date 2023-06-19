import json
import numpy as np

from typing import List, Optional

from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

from digital_twin.config.app_config import (
    NUM_RETURNED_VECTORDB_HITS,
    BATCH_SIZE_ENCODE_CHUNKS,  
    ENABLE_MINI_CHUNK,
)

from digital_twin.vectordb.chunking.models import InferenceChunk, EmbeddedIndexChunk, IndexChunk
from digital_twin.vectordb.interface import VectorDB, VectorDBFilter
from digital_twin.embedding.models import Embedder
from digital_twin.embedding.utils import split_chunk_text_into_mini_chunks, get_default_embedding_model
from digital_twin.server.model import SearchDoc
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time


logger = setup_logger()


def chunks_to_search_docs(chunks: list[InferenceChunk] | None) -> list[SearchDoc]:
    search_docs = (
        [
            SearchDoc(
                semantic_identifier=chunk.semantic_identifier,
                link=chunk.source_links.get(0) if chunk.source_links else None,
                blurb=chunk.blurb,
                source_type=chunk.source_type,
            )
            for chunk in chunks
        ]
        if chunks
        else []
    )
    return search_docs

@log_function_time()
def retrieve_documents(
    query: str,
    filters: Optional[List[VectorDBFilter]],
    vectordb: VectorDB,
    num_hits: int = NUM_RETURNED_VECTORDB_HITS,
) -> list[InferenceChunk] | None:
    top_chunks = vectordb.semantic_retrieval(query, filters, num_hits)
    if not top_chunks:
        filters_log_msg = json.dumps(filters, separators=(",", ":")).replace(
            "\n", ""
        )
        logger.warning(
            f"Semantic search returned no results with filters: {filters_log_msg}"
        )
        return None

    top_docs = [
        top_chunk.source_links[0]
        for top_chunk in top_chunks
        if top_chunk.source_links is not None
    ]
    files_log_msg = f"Top links from semantic search: {', '.join(top_docs)}"
    logger.info(files_log_msg)

    return top_chunks


@log_function_time()
def encode_chunks(
    chunks: list[IndexChunk],
    embedding_model: Embeddings | None = None,
    batch_size: int = BATCH_SIZE_ENCODE_CHUNKS,
    enable_mini_chunk: bool = ENABLE_MINI_CHUNK, # To Support Re-ranker model
) -> list[EmbeddedIndexChunk]:
    embedded_chunks: list[EmbeddedIndexChunk] = []
    if embedding_model is None:
        embedding_model = get_default_embedding_model()

    chunk_texts = []
    chunk_mini_chunks_count = {}
    for chunk_ind, chunk in enumerate(chunks):
        chunk_texts.append(chunk.content)
        mini_chunk_texts = (
            split_chunk_text_into_mini_chunks(chunk.content)
            if enable_mini_chunk
            else []
        )
        chunk_texts.extend(mini_chunk_texts)
        chunk_mini_chunks_count[chunk_ind] = 1 + len(mini_chunk_texts)

    text_batches = [
        chunk_texts[i : i + batch_size] for i in range(0, len(chunk_texts), batch_size)
    ]
    
    if isinstance(embedding_model, Embeddings):
        embeddings: list[list[float]] = embedding_model.embed_documents(text_batches[0])
    elif isinstance(embedding_model, SentenceTransformer):
        embeddings_np: list[np.ndarray] = []
        for text_batch in text_batches:
            embeddings_np.extend(embedding_model.encode(text_batch))
        embeddings: list[list[float]] = [embedding.tolist() for embedding in embeddings_np]
    else:
        raise ValueError(f"Unknown embedding model type: {type(embedding_model)}")

    embedding_ind_start = 0
    for chunk_ind, chunk in enumerate(chunks):
        num_embeddings = chunk_mini_chunks_count[chunk_ind]
        chunk_embeddings = embeddings[
            embedding_ind_start : embedding_ind_start + num_embeddings
        ]
        new_embedded_chunk = EmbeddedIndexChunk(
            **{k: getattr(chunk, k) for k in chunk.__dataclass_fields__},
            embeddings=chunk_embeddings,
        )
        embedded_chunks.append(new_embedded_chunk)
        embedding_ind_start += num_embeddings

    return embedded_chunks


class DefaultEmbedder(Embedder):
    def embed(self, chunks: list[IndexChunk]) -> list[EmbeddedIndexChunk]:
        return encode_chunks(chunks)