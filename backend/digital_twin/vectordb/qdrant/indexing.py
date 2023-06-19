import uuid
from uuid import UUID
from functools import partial

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.http.models.models import UpdateResult, UpdateStatus
from qdrant_client.models import (
    CollectionsResponse,
    Distance,
    PointStruct,
    VectorParams,
)

from digital_twin.config.constants import (
    BLURB,
    CHUNK_ID,
    CONTENT,
    DOCUMENT_ID,
    SECTION_CONTINUATION,
    SEMANTIC_IDENTIFIER,
    SOURCE_LINKS,
    SOURCE_TYPE,
    PUBLIC_DOC_PAT,
    ALLOWED_USERS,
    ALLOWED_GROUPS,
)

from digital_twin.config.app_config import DOC_EMBEDDING_DIM

from digital_twin.vectordb.chunking.models import EmbeddedIndexChunk
from digital_twin.vectordb.utils import (
    get_uuid_from_chunk, 
    update_doc_user_map,
    DEFAULT_BATCH_SIZE,
)


from digital_twin.utils.clients import get_qdrant_client
from digital_twin.utils.logging import setup_logger
logger = setup_logger()

def list_collections() -> CollectionsResponse:
    return get_qdrant_client().get_collections()


def create_collection(
    collection_name: str, embedding_dim: int = DOC_EMBEDDING_DIM
) -> None:
    logger.info(f"Attempting to create collection {collection_name}")
    result = get_qdrant_client().create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=embedding_dim, distance=Distance.COSINE
        ),
    )
    if not result:
        raise RuntimeError("Could not create Qdrant collection")


def recreate_collection(
    collection_name: str, embedding_dim: int = DOC_EMBEDDING_DIM
) -> None:
    logger.info(f"Attempting to recreate collection {collection_name}")
    result = get_qdrant_client().recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=embedding_dim, distance=Distance.COSINE
        ),
    )
    if not result:
        raise RuntimeError("Could not create Qdrant collection")


def delete_doc_chunks(
    document_id: str, collection_name: str, q_client: QdrantClient
) -> None:
    q_client.delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=DOCUMENT_ID,
                        match=models.MatchValue(value=document_id),
                    ),
                ],
            )
        ),
    )

def get_qdrant_document_whitelists(
    doc_chunk_id: str, collection_name: str, q_client: QdrantClient
) -> tuple[int, list[str], list[str]]:
    results = q_client.retrieve(
        collection_name=collection_name,
        ids=[doc_chunk_id],
        with_payload=[ALLOWED_USERS, ALLOWED_GROUPS],
    )
    if len(results) == 0:
        return 0, [], []
    payload = results[0].payload
    if not payload:
        raise RuntimeError(
            "Qdrant Index is corrupted, Document found with no access lists."
        )
    return len(results), payload[ALLOWED_USERS], payload[ALLOWED_GROUPS]



def delete_qdrant_doc_chunks(
    document_id: str, collection_name: str, q_client: QdrantClient
) -> bool:
    res = q_client.delete(
        collection_name=collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=DOCUMENT_ID,
                        match=models.MatchValue(value=document_id),
                    ),
                ],
            )
        ),
    )
    return True

def index_qdrant_chunks(
    chunks: list[EmbeddedIndexChunk],
    user_id: UUID | None,
    collection: str,
    client: QdrantClient | None = None,
    batch_upsert: bool = True,
) -> int:
    # Public documents will have the PUBLIC string in ALLOWED_USERS
    # If credential that kicked this off has no user associated, either Auth is off or the doc is public
    user_str = PUBLIC_DOC_PAT if user_id is None else str(user_id)
    q_client: QdrantClient = client if client else get_qdrant_client()

    point_structs: list[PointStruct] = []
    # Maps document id to dict of whitelists for users/groups each containing list of users/groups as strings
    doc_user_map: dict[str, dict[str, list[str]]] = {}
    docs_deleted = 0
    for chunk in chunks:
        document = chunk.source_document
        doc_user_map, delete_doc = update_doc_user_map(
            chunk,
            doc_user_map,
            partial(
                get_qdrant_document_whitelists,
                collection_name=collection,
                q_client=q_client,
            ),
            user_str,
        )

        if delete_doc:
            # Processing the first chunk of the doc and the doc exists
            docs_deleted += 1
            delete_qdrant_doc_chunks(document.id, collection, q_client)

        point_structs.extend(
            [
                PointStruct(
                    id=str(get_uuid_from_chunk(chunk, minichunk_ind)),
                    payload={
                        DOCUMENT_ID: document.id,
                        CHUNK_ID: chunk.chunk_id,
                        BLURB: chunk.blurb,
                        CONTENT: chunk.content,
                        SOURCE_TYPE: str(document.source.value),
                        SOURCE_LINKS: chunk.source_links,
                        SEMANTIC_IDENTIFIER: document.semantic_identifier,
                        SECTION_CONTINUATION: chunk.section_continuation,
                        ALLOWED_USERS: doc_user_map[document.id][ALLOWED_USERS],
                        ALLOWED_GROUPS: doc_user_map[document.id][ALLOWED_GROUPS],
                    },
                    vector=embedding,
                )
                for minichunk_ind, embedding in enumerate(chunk.embeddings)
            ]
        )

    if batch_upsert:
        point_struct_batches = [
            point_structs[x : x + DEFAULT_BATCH_SIZE]
            for x in range(0, len(point_structs), DEFAULT_BATCH_SIZE)
        ]
        for point_struct_batch in point_struct_batches:

            def upsert() -> UpdateResult | None:
                for _ in range(5):
                    try:
                        return q_client.upsert(
                            collection_name=collection, points=point_struct_batch
                        )
                    except ResponseHandlingException as e:
                        logger.warning(
                            f"Failed to upsert batch into qdrant due to error: {e}"
                        )
                return None

            index_results = upsert()
            log_status = index_results.status if index_results else "Failed"
            logger.info(
                f"Indexed {len(point_struct_batch)} chunks into Qdrant collection '{collection}', "
                f"status: {log_status}"
            )
    else:
        index_results = q_client.upsert(
            collection_name=collection, points=point_structs
        )
        logger.info(
            f"Document batch of size {len(point_structs)} indexing status: {index_results.status}"
        )

    return len(doc_user_map.keys()) - docs_deleted
    

