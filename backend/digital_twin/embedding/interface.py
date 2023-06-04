import json
from typing import List, Optional

from langchain.embeddings.base import Embeddings
from langchain.embeddings import OpenAIEmbeddings



from digital_twin.config.app_config import NUM_RETURNED_VECTORDB_HITS
from digital_twin.config.model_config import map_model_platform_to_db_api_key_type
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time
from digital_twin.llm.config import get_api_key
from digital_twin.llm.interface import SelectedModelConfig
from digital_twin.vectordb.chunking.models import InferenceChunk
from digital_twin.vectordb.interface import VectorDB, VectorDBFilter

logger = setup_logger()


_EMBED_MODEL: Optional[Embeddings] = None

# TODO: Make this into a proper Embedder class
def get_default_embedding_model(
    user_id: str,
    model_config: SelectedModelConfig, **kwargs
) -> Embeddings:
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        openai_api_key = get_api_key(
            user_id,
            model_config.platform,
        )
        _EMBED_MODEL = OpenAIEmbeddings(openai_api_key=openai_api_key)
    return _EMBED_MODEL

#TODO: Use re-ranker (possibly use Cohere's re-ranker)

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
