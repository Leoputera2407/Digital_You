import json
import typesense  # type: ignore

from typesense.exceptions import ObjectNotFound  # type: ignore
from functools import partial
from typing import Any
from uuid import UUID


from digital_twin.config.app_config import TYPESENSE_DEFAULT_COLLECTION, NUM_RETURNED_HITS
from digital_twin.config.constants import (
    ALLOWED_USERS,
    ALLOWED_GROUPS,
    BLURB,
    CHUNK_ID,
    CONTENT,
    DOCUMENT_ID,
    PUBLIC_DOC_PAT,
    SECTION_CONTINUATION,
    SEMANTIC_IDENTIFIER,
    SOURCE_LINKS,
    SOURCE_TYPE,
    METADATA,
)
from digital_twin.indexdb.utils import (
    DEFAULT_BATCH_SIZE, 
    get_uuid_from_chunk,
    update_doc_user_map,
)
from digital_twin.indexdb.chunking.models import (
    IndexType,
    EmbeddedIndexChunk,
    IndexChunk,
    InferenceChunk,
)
from digital_twin.indexdb.interface import (
    IndexDBFilter, 
    KeywordIndex,
)
from digital_twin.utils.clients import get_typesense_client
from digital_twin.utils.logging import setup_logger



logger = setup_logger()


def check_typesense_collection_exist(
    collection_name: str = TYPESENSE_DEFAULT_COLLECTION,
) -> bool:
    client = get_typesense_client()
    try:
        client.collections[collection_name].retrieve()
    except ObjectNotFound:
        return False
    return True


def create_typesense_collection(
    collection_name: str = TYPESENSE_DEFAULT_COLLECTION,
) -> None:
    ts_client = get_typesense_client()
    collection_schema = {
        "name": collection_name,
        "fields": [
            # Typesense uses "id" type string as a special field
            {"name": "id", "type": "string"},
            {"name": DOCUMENT_ID, "type": "string"},
            {"name": CHUNK_ID, "type": "int32"},
            {"name": BLURB, "type": "string"},
            {"name": CONTENT, "type": "string"},
            {"name": SOURCE_TYPE, "type": "string"},
            {"name": SOURCE_LINKS, "type": "string"},
            {"name": SEMANTIC_IDENTIFIER, "type": "string"},
            {"name": SECTION_CONTINUATION, "type": "bool"},
            {"name": ALLOWED_USERS, "type": "string[]"},
            {"name": ALLOWED_GROUPS, "type": "string[]"},
        ],
    }
    ts_client.collections.create(collection_schema)


def get_typesense_document_whitelists(
    doc_chunk_id: str, collection_name: str, ts_client: typesense.Client
) -> tuple[bool, list[str], list[str]]:
    """Returns whether the document already exists and the users/group whitelists"""
    try:
        document = (
            ts_client.collections[collection_name].documents[doc_chunk_id].retrieve()
        )
    except ObjectNotFound:
        return False, [], []
    if document[ALLOWED_USERS] is None or document[ALLOWED_GROUPS] is None:
        raise RuntimeError(
            "Typesense Index is corrupted, Document found with no access lists."
        )
    return True, document[ALLOWED_USERS], document[ALLOWED_GROUPS]


def delete_typesense_doc_chunks(
    document_id: str, collection_name: str, ts_client: typesense.Client
) -> bool:
    doc_id_filter = {"filter_by": f"{DOCUMENT_ID}:'{document_id}'"}

    # Typesense doesn't seem to prioritize individual deletions, problem not seen with this approach
    # Point to consider if we see instances of number of Typesense and Qdrant docs not matching
    del_result = ts_client.collections[collection_name].documents.delete(doc_id_filter)
    return del_result["num_deleted"] != 0


def index_typesense_chunks(
    chunks: list[IndexChunk | EmbeddedIndexChunk],
    user_id: UUID | None,
    collection: str,
    client: typesense.Client | None = None,
    batch_upsert: bool = True,
) -> int:
    user_str = PUBLIC_DOC_PAT if user_id is None else str(user_id)
    ts_client: typesense.Client = client if client else get_typesense_client()

    new_documents: list[dict[str, Any]] = []
    doc_user_map: dict[str, dict[str, list[str]]] = {}
    docs_deleted = 0
    for chunk in chunks:
        document = chunk.source_document
        doc_user_map, delete_doc = update_doc_user_map(
            chunk,
            doc_user_map,
            partial(
                get_typesense_document_whitelists,
                collection_name=collection,
                ts_client=ts_client,
            ),
            user_str,
        )

        if delete_doc:
            # Processing the first chunk of the doc and the doc exists
            docs_deleted += 1
            delete_typesense_doc_chunks(document.id, collection, ts_client)

        new_documents.append(
            {
                "id": str(get_uuid_from_chunk(chunk)),  # No minichunks for typesense
                DOCUMENT_ID: document.id,
                CHUNK_ID: chunk.chunk_id,
                BLURB: chunk.blurb,
                CONTENT: chunk.content,
                SOURCE_TYPE: str(document.source.value),
                SOURCE_LINKS: json.dumps(chunk.source_links),
                SEMANTIC_IDENTIFIER: document.semantic_identifier,
                SECTION_CONTINUATION: chunk.section_continuation,
                ALLOWED_USERS: doc_user_map[document.id][ALLOWED_USERS],
                ALLOWED_GROUPS: doc_user_map[document.id][ALLOWED_GROUPS],
            }
        )

    if batch_upsert:
        doc_batches = [
            new_documents[x : x + DEFAULT_BATCH_SIZE]
            for x in range(0, len(new_documents), DEFAULT_BATCH_SIZE)
        ]
        for doc_batch in doc_batches:
            results = ts_client.collections[collection].documents.import_(
                doc_batch, {"action": "upsert"}
            )
            failures = [
                doc_res["success"]
                for doc_res in results
                if doc_res["success"] is not True
            ]
            logger.info(
                f"Indexed {len(doc_batch)} chunks into Typesense collection '{collection}', "
                f"number failed: {len(failures)}"
            )
    else:
        [
            ts_client.collections[collection].documents.upsert(document)
            for document in new_documents
        ]

    return len(doc_user_map.keys()) - docs_deleted


def _build_typesense_filters(
    user_id: UUID | None, filters: list[IndexDBFilter] | None
) -> str:
    filter_str = ""

    # Permissions filter
    if user_id:
        filter_str += f"{ALLOWED_USERS}:=[{PUBLIC_DOC_PAT},{user_id}] && "
    else:
        filter_str += f"{ALLOWED_USERS}:={PUBLIC_DOC_PAT} && "

    # Provided query filters
    if filters:
        for filter_dict in filters:
            valid_filters = {
                key: value for key, value in filter_dict.items() if value is not None
            }
            for filter_key, filter_val in valid_filters.items():
                if isinstance(filter_val, str):
                    filter_str += f"{filter_key}:={filter_val} && "
                elif isinstance(filter_val, list):
                    filters_or = ",".join([str(f_val) for f_val in filter_val])
                    filter_str += f"{filter_key}:=[{filters_or}] && "
                else:
                    raise ValueError("Invalid filters provided")
    if filter_str[-4:] == " && ":
        filter_str = filter_str[:-4]
    return filter_str


class TypesenseIndex(KeywordIndex):
    def __init__(self, collection: str = TYPESENSE_DEFAULT_COLLECTION) -> None:
        self.collection = collection
        self.ts_client = get_typesense_client()

    def index(self, chunks: list[IndexChunk], user_id: UUID | None) -> int:
        return index_typesense_chunks(
            chunks=chunks,
            user_id=user_id,
            collection=self.collection,
            client=self.ts_client,
        )

    def keyword_search(
        self,
        query: str,
        user_id: UUID | None,
        filters: list[IndexDBFilter] | None,
        num_to_retrieve: int = NUM_RETURNED_HITS,
    ) -> list[InferenceChunk]:
        filters_str = _build_typesense_filters(user_id, filters)

        search_query = {
            "q": query,
            # Often, data_source semantic identifiers are file names or title or summaries
            "query_by": f"{CONTENT}, {SEMANTIC_IDENTIFIER}",
            "query_by_weight": "1,3",
            "filter_by": filters_str,
            "per_page": num_to_retrieve,
            "limit_hits": num_to_retrieve,
            "num_typos": 2,
            "prefix": "false",
            # below is required to allow proper partial matching of a query
            # (partial matching = only some of the terms in the query match)
            # more info here: https://typesense-community.slack.com/archives/C01P749MET0/p1688083239192799
            "exhaustive_search": "true",
        }

        search_results = self.ts_client.collections[self.collection].documents.search(
            search_query
        )

        hits = search_results["hits"]
        inference_chunks = [
            InferenceChunk.from_dict(
                hit["document"],
                hit.get("text_match_info", None),
                IndexType.TYPESENSE.value,
            ) for hit in hits]

        return inference_chunks
