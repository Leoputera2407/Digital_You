from collections import defaultdict
from typing import Dict, List, Optional, Union, cast

from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from sentence_transformers import CrossEncoder  # type: ignore
from sentence_transformers import SentenceTransformer

from digital_twin.config.app_config import EMBEDDING_OPENAI_API_KEY, MINI_CHUNK_SIZE
from digital_twin.indexdb.chunking.models import InferenceChunk

_EMBED_MODEL: Optional[Embeddings | SentenceTransformer] = None


def chunks_to_search_docs(chunks: list[InferenceChunk] | None):
    from digital_twin.server.model import SearchDoc

    search_docs = (
        [
            SearchDoc(
                semantic_identifier=chunk.semantic_identifier if chunk.semantic_identifier else "",
                link=chunk.source_links.get(0) if chunk.source_links else None,
                blurb=chunk.blurb,
                source_type=chunk.source_type,
            )
            for chunk in chunks
            if chunk.semantic_identifier
        ]
        if chunks
        else []
    )
    return search_docs


def split_chunk_text_into_mini_chunks(chunk_text: str, mini_chunk_size: int = MINI_CHUNK_SIZE) -> list[str]:
    chunks = []
    start = 0
    separators = [" ", "\n", "\r", "\t"]

    while start < len(chunk_text):
        if len(chunk_text) - start <= mini_chunk_size:
            end = len(chunk_text)
        else:
            # Find the first separator character after min_chunk_length
            end_positions = [(chunk_text[start + mini_chunk_size :]).find(sep) for sep in separators]
            # Filter out the not found cases (-1)
            end_positions = [pos for pos in end_positions if pos != -1]
            if not end_positions:
                # If no more separators, the rest of the string becomes a chunk
                end = len(chunk_text)
            else:
                # Add min_chunk_length and start to the end position
                end = min(end_positions) + start + mini_chunk_size

        chunks.append(chunk_text[start:end])
        start = end + 1  # Move to the next character after the separator

    return chunks


def get_default_embedding_model(**kwargs) -> Union[Embeddings, SentenceTransformer]:
    """
    In general, we should have control over what embedding to use.
    """
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = OpenAIEmbeddings(openai_api_key=EMBEDDING_OPENAI_API_KEY)
    return _EMBED_MODEL


def perform_reciprocal_rank_fusion(
    semantic_top_chunks: Optional[List[InferenceChunk]],
    keyword_top_chunks: Optional[List[InferenceChunk]],
    keyword_weight: float,
) -> Optional[List[InferenceChunk]]:
    """
    Perform Reciprocal Rank Fusion on search results.
    Note: if one of the search results is None or empty,
             the other search results will be returned.

    Combining search results in a rank-aware manner is better than a simple list merge
    https://arxiv.org/pdf/2010.00200.pdf
    https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

    Args:
    semantic_top_chunks (List[InferenceChunk]): List of search results from the semantic search.
    keyword_top_chunks (List[InferenceChunk]): List of search results from the keyword search.
    keyword_weight (float): Weight given to the keyword search in the RRF calculation.

    Returns:
    List[InferenceChunk]: List of top reranked search results.
    """
    if not semantic_top_chunks and not keyword_top_chunks:
        raise ValueError("Both semantic_top_chunks and keyword_top_chunks cannot be None or empty.")
    if not semantic_top_chunks:
        return keyword_top_chunks
    if not keyword_top_chunks:
        return semantic_top_chunks

    # Create lists of dicts with document data for RRF.
    semantic_search_data = [
        {"id": chunk.document_id, "rank": i, "chunk": chunk} for i, chunk in enumerate(semantic_top_chunks)
    ]
    keyword_search_data = [
        {"id": chunk.document_id, "rank": i, "chunk": chunk} for i, chunk in enumerate(keyword_top_chunks)
    ]

    # Create mapping from id to chunk
    id_to_chunk_map = {chunk.document_id: chunk for chunk in semantic_top_chunks + keyword_top_chunks}

    # Perform the Reciprocal Rank Fusion
    combined_ranks: Dict[str, float] = defaultdict(float)

    # Update the RRF scores for documents in keyword_search_data
    for item in semantic_search_data:
        sem_chunk = cast(str, item["id"])
        sem_rank = cast(int, item["rank"])
        combined_ranks[sem_chunk] += keyword_weight / (sem_rank + 1)

    # Update the RRF scores for documents in semantic_search_data
    for item in keyword_search_data:
        key_chunk = cast(str, item["id"])
        key_rank = cast(int, item["rank"])
        combined_ranks[key_chunk] += (1 - keyword_weight) / (key_rank + 1)

    # Sort the combined ranks in descending order
    combined_ranks_sorted = sorted(combined_ranks.items(), key=lambda item: item[1], reverse=True)

    # Extract the top 'num_rerank' documents
    top_reranked_chunks = [id_to_chunk_map[item[0]] for item in combined_ranks_sorted]

    return top_reranked_chunks


"""" Local Model Experiment, really bad compared to Cohere
from digital_twin.utils.timing import log_function_time
from digital_twin.utils.logging import setup_logger

logger = setup_logger()
_RERANK_MODELS: None | list[CrossEncoder] = None

# https://www.sbert.net/docs/pretrained-models/ce-msmarco.html
CROSS_ENCODER_MODEL_ENSEMBLE = [
    "cross-encoder/ms-marco-MiniLM-L-4-v2",
    "cross-encoder/ms-marco-TinyBERT-L-2-v2",
]

CROSS_EMBED_CONTEXT_SIZE = 512

def get_default_reranking_model_ensemble() -> list[CrossEncoder]:
    global _RERANK_MODELS
    if _RERANK_MODELS is None:
        _RERANK_MODELS = [
            CrossEncoder(model_name) for model_name in CROSS_ENCODER_MODEL_ENSEMBLE
        ]
        for model in _RERANK_MODELS:
            model.max_length = CROSS_EMBED_CONTEXT_SIZE
    return _RERANK_MODELS



@log_function_time()
def local_model_test_reranking( 
    query: str,
    chunks: list[InferenceChunk],
) -> list[InferenceChunk]:
    cross_encoders = get_default_reranking_model_ensemble()
    sim_scores = sum([encoder.predict([(query, chunk['content']) for chunk in chunks]) for encoder in cross_encoders])  # type: ignore
    scored_results = list(zip(sim_scores, chunks))
    scored_results.sort(key=lambda x: x[0], reverse=True)
    ranked_sim_scores, ranked_chunks = zip(*scored_results)
    print(f"Reranked similarity scores: {str(ranked_sim_scores)}")
    logger.debug(f"Reranked similarity scores: {str(ranked_sim_scores)}")

    return ranked_chunks


def warm_up_models() -> None:
    warm_up_str = "Test stuff"
    cross_encoders = get_default_reranking_model_ensemble()
    [
        cross_encoder.predict((warm_up_str, warm_up_str))
        for cross_encoder in cross_encoders
    ]
"""
