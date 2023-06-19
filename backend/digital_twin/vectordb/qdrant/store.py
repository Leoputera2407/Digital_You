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

from digital_twin.config.app_config import QDRANT_DEFAULT_COLLECTION
from digital_twin.config.constants import ALLOWED_USERS, PUBLIC_DOC_PAT
from digital_twin.embedding.interface import get_default_embedding_model
from digital_twin.utils.clients import get_qdrant_client
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time
from digital_twin.vectordb.chunking.models import (
    EmbeddedIndexChunk,
    InferenceChunk,
)
from digital_twin.vectordb.interface import VectorDB, VectorDBFilter
from digital_twin.vectordb.qdrant.indexing import index_chunks

logger = setup_logger()


class QdrantDatastore(VectorDB):
    def __init__(self, collection: str = QDRANT_DEFAULT_COLLECTION) -> None:
        self.collection = collection
        self.client = get_qdrant_client()

    def index(self, chunks: list[EmbeddedIndexChunk], user_id: int | None) -> bool:
        return index_chunks(
            chunks=chunks,
            user_id=user_id,
            collection=self.collection,
            client=self.client,
        )

    @log_function_time()
    def semantic_retrieval(
        self,
        query: str,
        user_id: int | None,
        filters: list[VectorDBFilter] | None,
        num_to_retrieve: int,
    ) -> list[InferenceChunk]:
        query_embedding = get_default_embedding_model().encode(
            query
        )  # TODO: make this part of the embedder interface
        if not isinstance(query_embedding, list):
            query_embedding = query_embedding.tolist()

        hits = []
        filter_conditions = []
        try:
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
                        key: value
                        for key, value in filter_dict.items()
                        if value is not None
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

            hits = self.client.search(
                collection_name=self.collection,
                query_vector=query_embedding,
                query_filter=Filter(must=list(filter_conditions)),
                limit=num_to_retrieve,
            )
        except ResponseHandlingException as e:
            logger.exception(f'Qdrant querying failed due to: "{e}", is Qdrant set up?')
        except UnexpectedResponse as e:
            logger.exception(
                f'Qdrant querying failed due to: "{e}", has ingestion been run?'
            )
        return [
            InferenceChunk.from_dict(hit.payload)
            for hit in hits
            if hit.payload is not None
        ]

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
