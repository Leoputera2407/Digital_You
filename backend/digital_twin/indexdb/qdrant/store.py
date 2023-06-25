from uuid import UUID
from langchain.embeddings.base import Embeddings

from qdrant_client.http.exceptions import (
    ResponseHandlingException,
    UnexpectedResponse,
)
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
)

from digital_twin.config.app_config import QDRANT_DEFAULT_COLLECTION, NUM_RETURNED_HITS, SEARCH_DISTANCE_CUTOFF
from digital_twin.config.constants import ALLOWED_USERS, PUBLIC_DOC_PAT

from digital_twin.search.interface import get_default_embedding_model
from digital_twin.indexdb.utils import get_uuid_from_chunk
from digital_twin.indexdb.chunking.models import (
    EmbeddedIndexChunk,
    InferenceChunk,
)
from digital_twin.indexdb.interface import VectorIndexDB, IndexFilter
from digital_twin.indexdb.qdrant.indexing import index_qdrant_chunks
from digital_twin.utils.clients import get_qdrant_client
from digital_twin.utils.timing import log_function_time
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


def _build_qdrant_filters(
    user_id: UUID | None, filters: list[IndexFilter] | None
) -> list[FieldCondition]:
    filter_conditions: list[FieldCondition] = []
    # Permissions filter
    if user_id:
        filter_conditions.append(
            FieldCondition(
                key=ALLOWED_USERS,
                match=MatchAny(any=[str(user_id), PUBLIC_DOC_PAT]),
            )
        )
    else:
        filter_conditions.append(
            FieldCondition(
                key=ALLOWED_USERS,
                match=MatchValue(value=PUBLIC_DOC_PAT),
            )
        )

    # Provided query filters
    if filters:
        for filter_dict in filters:
            valid_filters = {
                key: value for key, value in filter_dict.items() if value is not None
            }
            for filter_key, filter_val in valid_filters.items():
                if isinstance(filter_val, str):
                    filter_conditions.append(
                        FieldCondition(
                            key=filter_key,
                            match=MatchValue(value=filter_val),
                        )
                    )
                elif isinstance(filter_val, list):
                    filter_conditions.append(
                        FieldCondition(
                            key=filter_key,
                            match=MatchAny(any=filter_val),
                        )
                    )
                else:
                    raise ValueError("Invalid filters provided")

    return filter_conditions


class QdrantVectorDB(VectorIndexDB):
    def __init__(self, collection: str = QDRANT_DEFAULT_COLLECTION) -> None:
        self.collection = collection
        self.client = get_qdrant_client()

    def index(self, chunks: list[EmbeddedIndexChunk], user_id: UUID | None) -> int:
        return index_qdrant_chunks(
            chunks=chunks,
            user_id=user_id,
            collection=self.collection,
            client=self.client,
        )

    @log_function_time()
    def semantic_retrieval(
        self,
        query: str,
        user_id: UUID | None,
        filters: list[IndexFilter] | None,
        num_to_retrieve: int = NUM_RETURNED_HITS,
        page_size: int = NUM_RETURNED_HITS,
        distance_cutoff: float | None = SEARCH_DISTANCE_CUTOFF,
    ) -> list[InferenceChunk]:
        embedding_model = get_default_embedding_model()

        if isinstance(embedding_model, Embeddings):
            query_embedding = embedding_model.embed_query(
                query
            )
        else:
            query_embedding = embedding_model.encode(
                query
            )  # TODO: make this part of the embedder interface

        if not isinstance(query_embedding, list):
            query_embedding = query_embedding.tolist()

        filter_conditions = _build_qdrant_filters(user_id, filters)

        page_offset = 0
        found_inference_chunks: list[InferenceChunk] = []
        found_chunk_uuids: set[UUID] = set()
        while len(found_inference_chunks) < num_to_retrieve:
            try:
                hits = self.client.search(
                    collection_name=self.collection,
                    query_vector=query_embedding,
                    query_filter=Filter(must=list(filter_conditions)),
                    limit=page_size,
                    offset=page_offset,
                    score_threshold=distance_cutoff,
                )
                page_offset += page_size
                if not hits:
                    break
            except ResponseHandlingException as e:
                logger.exception(
                    f'Qdrant querying failed due to: "{e}", is Qdrant set up?'
                )
                break
            except UnexpectedResponse as e:
                logger.exception(
                    f'Qdrant querying failed due to: "{e}", has ingestion been run?'
                )
                break

            inference_chunks_from_hits = [
                InferenceChunk.from_dict(hit.payload)
                for hit in hits
                if hit.payload is not None
            ]
            for inf_chunk in inference_chunks_from_hits:
                # remove duplicate chunks which happen if minichunks are used
                inf_chunk_id = get_uuid_from_chunk(inf_chunk)
                if inf_chunk_id not in found_chunk_uuids:
                    found_inference_chunks.append(inf_chunk)
                    found_chunk_uuids.add(inf_chunk_id)

        return found_inference_chunks

    def get_from_id(self, object_id: str) -> InferenceChunk | None:
        matches, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="id", match=MatchValue(value=object_id))]
            ),
        )
        if not matches:
            return None

        if len(matches) > 1:
            logger.error(f"Found multiple matches for {logger}: {matches}")

        match = matches[0]
        if not match.payload:
            return None

        return InferenceChunk.from_dict(match.payload)
