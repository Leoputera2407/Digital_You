
from typing import Optional, Union
from langchain.embeddings.base import Embeddings
from langchain.embeddings import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder  # type: ignore

from digital_twin.config.app_config import MINI_CHUNK_SIZE, EMBEDDING_OPENAI_API_KEY
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.server.model import SearchDoc


_EMBED_MODEL: Optional[Embeddings | SentenceTransformer] = None


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


def split_chunk_text_into_mini_chunks(
    chunk_text: str, mini_chunk_size: int = MINI_CHUNK_SIZE
) -> list[str]:
    chunks = []
    start = 0
    separators = [" ", "\n", "\r", "\t"]

    while start < len(chunk_text):
        if len(chunk_text) - start <= mini_chunk_size:
            end = len(chunk_text)
        else:
            # Find the first separator character after min_chunk_length
            end_positions = [
                (chunk_text[start + mini_chunk_size :]).find(sep) for sep in separators
            ]
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


def get_default_embedding_model(
    **kwargs
) -> Union[Embeddings, SentenceTransformer]:
    """
    In general, we should have control over what embedding to use.
    """
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = OpenAIEmbeddings(
            openai_api_key=EMBEDDING_OPENAI_API_KEY
        )
    return _EMBED_MODEL

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

from digital_twin.utils.logging import setup_logger
from multiprocessing import Pool

logger = setup_logger()

def local_model_test_reranking( 
    query: str,
    chunks: list[InferenceChunk],
) -> list[InferenceChunk]:
    cross_encoders = get_default_reranking_model_ensemble()
    sim_scores = sum([encoder.predict([(query, chunk.content) for chunk in chunks]) for encoder in cross_encoders])  # type: ignore
    scored_results = list(zip(sim_scores, chunks))
    scored_results.sort(key=lambda x: x[0], reverse=True)
    ranked_sim_scores, ranked_chunks = zip(*scored_results)

    logger.debug(f"Reranked similarity scores: {str(ranked_sim_scores)}")

    return ranked_chunks

def local_model_test_reranking_multiprocessing(
    query: str,
    chunks: list[InferenceChunk],
) -> list[InferenceChunk]:
    def cross_encoder_predict(args):
        query, chunk_content, encoder_model = args
        return encoder_model.predict((query, chunk_content))
    
    cross_encoders = get_default_reranking_model_ensemble()
   
    # Create a pool of processes. By default, one is created for each CPU in your machine.
    with Pool() as p:
        sim_scores = sum(
            p.map(cross_encoder_predict, [(query, chunk.content, encoder_model) for chunk in chunks for encoder_model in cross_encoders])
        )
    
    scored_results = list(zip(sim_scores, chunks))
    scored_results.sort(key=lambda x: x[0], reverse=True)
    ranked_sim_scores, ranked_chunks = zip(*scored_results)

    logger.debug(f"Reranked similarity scores: {str(ranked_sim_scores)}")

    return ranked_chunks


def warm_up_models() -> None:
    warm_up_str = "Test stuff"
    cross_encoders = get_default_reranking_model_ensemble()
    [
        cross_encoder.predict((warm_up_str, warm_up_str))
        for cross_encoder in cross_encoders
    ]