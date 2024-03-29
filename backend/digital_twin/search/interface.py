import asyncio
import json
from typing import List, Optional
from uuid import UUID

import cohere
import numpy as np
from cohere.responses.rerank import RerankResult
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

from digital_twin.config.app_config import (
    BATCH_SIZE_ENCODE_CHUNKS,
    COHERE_KEY,
    ENABLE_MINI_CHUNK,
    NUM_RERANKED_RESULTS,
    NUM_RETURNED_HITS,
)
from digital_twin.indexdb.chunking.models import EmbeddedIndexChunk, IndexChunk, InferenceChunk
from digital_twin.indexdb.interface import IndexDBFilter, KeywordIndex, VectorIndexDB
from digital_twin.search.keyword_utils import keyword_search_query_processing
from digital_twin.search.models import Embedder
from digital_twin.search.utils import (
    get_default_embedding_model,
    perform_reciprocal_rank_fusion,
    split_chunk_text_into_mini_chunks,
)
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()


class DefaultEmbedder(Embedder):
    def embed(self, chunks: list[IndexChunk]) -> list[EmbeddedIndexChunk]:
        return encode_chunks(chunks)


@log_function_time()
def semantic_reranking(
    query: str, chunks: list[InferenceChunk], num_rerank: int = NUM_RERANKED_RESULTS
) -> list[InferenceChunk]:
    """
    Rerank the chunks based on the semantic similarity between the query and the chunks
    """
    co = cohere.Client(COHERE_KEY)
    _documents = [chunk.content for chunk in chunks]

    results: List[RerankResult] = co.rerank(
        query=query, documents=_documents, top_n=num_rerank, model="rerank-english-v2.0"
    )
    reranked_chunks = []
    for r in results:
        doc = chunks[r.index]
        doc.score_info["rerank_score"] = r.relevance_score
        reranked_chunks.append(doc)
    return reranked_chunks


@log_function_time()
def retrieve_semantic_documents(
    query: str,
    user_id: UUID | None,
    filters: Optional[List[IndexDBFilter]],
    vectordb: VectorIndexDB,
    num_hits: int = NUM_RETURNED_HITS,
) -> List[InferenceChunk] | None:
    """
    This is purely a semantic search

    :return: top_chunks
    """
    top_chunks = vectordb.semantic_retrieval(query, user_id, filters, num_hits)
    if not top_chunks:
        filters_log_msg = json.dumps(filters, separators=(",", ":")).replace("\n", "")
        logger.warning(f"Semantic search returned no results with filters: {filters_log_msg}")
        return None
    return top_chunks


@log_function_time()
def retrieve_keyword_documents(
    query: str,
    user_id: UUID | None,
    filters: list[IndexDBFilter] | None,
    datastore: KeywordIndex,
    num_hits: int = NUM_RETURNED_HITS,
) -> list[InferenceChunk] | None:
    """
    This is purely a keyword search

    :return: top_chunks
    """
    edited_query = keyword_search_query_processing(query)
    top_chunks = datastore.keyword_search(edited_query, user_id, filters, num_hits)
    if not top_chunks:
        filters_log_msg = json.dumps(filters, separators=(",", ":")).replace("\n", "")
        logger.warning(
            f"Keyword search returned no results...\nfilters: {filters_log_msg}\nedited query: {edited_query}"
        )
        return None
    return top_chunks


@log_function_time()
def retrieve_semantic_reranked_documents(
    query: str,
    user_id: UUID | None,
    filters: Optional[List[IndexDBFilter]],
    vectordb: VectorIndexDB,
    num_hits: int = NUM_RETURNED_HITS,
    num_rerank: int = NUM_RERANKED_RESULTS,
) -> tuple[list[InferenceChunk] | None, list[InferenceChunk] | None] | None:
    """
    This is for semantic serach + reranking

    :return: tuple of (re-ranked chunks, the rest of the top chunks)
    """
    top_chunks = vectordb.semantic_retrieval(query, user_id, filters, num_hits)
    if not top_chunks:
        filters_log_msg = json.dumps(filters, separators=(",", ":")).replace("\n", "")
        logger.warning(f"Semantic search returned no results with filters: {filters_log_msg}")
        return None

    ranked_chunks = semantic_reranking(query, top_chunks[:num_rerank], num_rerank)

    top_docs = [
        ranked_chunk.source_links[0]
        for ranked_chunk in ranked_chunks
        if ranked_chunk.source_links is not None
    ]
    files_log_msg = f"Top links from semantic search: {', '.join(top_docs)}"
    logger.info(files_log_msg)

    return ranked_chunks, top_chunks[num_rerank:]


@log_function_time()
async def async_retrieve_hybrid_reranked_documents(
    query: str,
    user_id: UUID | None,
    filters: Optional[List[IndexDBFilter]],
    vectordb: VectorIndexDB,
    keywordb: KeywordIndex,
    num_hits: int = NUM_RETURNED_HITS,
    num_rerank: int = NUM_RERANKED_RESULTS,
) -> tuple[list[InferenceChunk] | None, list[InferenceChunk] | None]:
    """
    This is for hybrid (semantic serach + keyword) with reranking

    :return: tuple of (re-ranked chunks, the rest of the top chunks)
    """
    # Typesense and qdrant clients are not co-routines,
    # they don't expose an async connection
    # So, we will perform async by running them in separate threads.
    loop = asyncio.get_event_loop()
    edited_query = keyword_search_query_processing(query)
    semantic_top_chunks_future = loop.run_in_executor(
        None, retrieve_semantic_documents, query, user_id, filters, vectordb, num_hits
    )
    keyword_top_chunks_future = loop.run_in_executor(
        None,
        retrieve_keyword_documents,
        edited_query,
        user_id,
        filters,
        keywordb,
        num_hits,
    )

    semantic_top_chunks, keyword_top_chunks = await asyncio.gather(
        semantic_top_chunks_future,
        keyword_top_chunks_future,
    )
    if not semantic_top_chunks and not keyword_top_chunks:
        logger.warning("Both semantic_top_chunks and keyword_top_chunks are empty.")
        return None, None

    rrf_combined_chunks = perform_reciprocal_rank_fusion(
        semantic_top_chunks, keyword_top_chunks, keyword_weight=0.3
    )
    if rrf_combined_chunks is None:
        logger.warning("Both semantic_top_chunks and keyword_top_chunks are empty.")
        return None, None
    ranked_chunks = semantic_reranking(query, rrf_combined_chunks[:num_rerank], num_rerank)

    top_docs = [
        ranked_chunk.source_links[0]
        for ranked_chunk in ranked_chunks
        if ranked_chunk.source_links is not None
    ]
    files_log_msg = f"Top links from semantic search: {', '.join(top_docs)}"
    logger.info(files_log_msg)

    return ranked_chunks, rrf_combined_chunks[len(ranked_chunks) :]


@log_function_time()
def encode_chunks(
    chunks: list[IndexChunk],
    embedding_model: Embeddings | None = None,
    batch_size: int = BATCH_SIZE_ENCODE_CHUNKS,
    enable_mini_chunk: bool = ENABLE_MINI_CHUNK,  # To Support Re-ranker model
) -> list[EmbeddedIndexChunk]:
    embedded_chunks: list[EmbeddedIndexChunk] = []
    if embedding_model is None:
        embedding_model = get_default_embedding_model()

    chunk_texts = []
    chunk_mini_chunks_count = {}
    for chunk_ind, chunk in enumerate(chunks):
        chunk_texts.append(chunk.content)
        mini_chunk_texts = split_chunk_text_into_mini_chunks(chunk.content) if enable_mini_chunk else []
        chunk_texts.extend(mini_chunk_texts)
        chunk_mini_chunks_count[chunk_ind] = 1 + len(mini_chunk_texts)

    text_batches = [chunk_texts[i : i + batch_size] for i in range(0, len(chunk_texts), batch_size)]
    embeddings: list[list[float]] = []
    if isinstance(embedding_model, Embeddings):
        for text_batch in text_batches:
            embeddings.extend(embedding_model.embed_documents(text_batch))
    elif isinstance(embedding_model, SentenceTransformer):
        embeddings_np: list[np.ndarray] = []
        for text_batch in text_batches:
            embeddings_np.extend(embedding_model.encode(text_batch))
        embeddings = [embedding.tolist() for embedding in embeddings_np]
    else:
        raise ValueError(f"Unknown embedding model type: {type(embedding_model)}")

    embedding_ind_start = 0
    for chunk_ind, chunk in enumerate(chunks):
        num_embeddings = chunk_mini_chunks_count[chunk_ind]
        chunk_embeddings = embeddings[embedding_ind_start : embedding_ind_start + num_embeddings]
        new_embedded_chunk = EmbeddedIndexChunk(
            **{k: getattr(chunk, k) for k in chunk.__dataclass_fields__},
            embeddings=chunk_embeddings,
        )
        embedded_chunks.append(new_embedded_chunk)
        embedding_ind_start += num_embeddings

    return embedded_chunks
