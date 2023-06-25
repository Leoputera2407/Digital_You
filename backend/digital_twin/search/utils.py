
from typing import Optional, Union
from langchain.embeddings.base import Embeddings
from langchain.embeddings import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer

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