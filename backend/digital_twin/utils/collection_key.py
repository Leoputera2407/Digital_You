from typing import Tuple
from uuid import uuid4

from digital_twin.indexdb.typesense.store import check_typesense_collection_exist
from digital_twin.indexdb.qdrant.indexing import list_collections as qdrant_list_collections

def get_unique_collection_keys() -> Tuple[str, str]:
    typesense_collection_key = str(uuid4())
    qdrant_collection_key = str(uuid4())

    while check_typesense_collection_exist(typesense_collection_key):  # Keep generating keys while the key exists
        typesense_collection_key = str(uuid4())

    while qdrant_collection_key in [collection.name for collection in qdrant_list_collections().collections]:
        qdrant_collection_key = str(uuid4())

    return typesense_collection_key, qdrant_collection_key