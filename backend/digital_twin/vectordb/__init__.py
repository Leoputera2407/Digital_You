from typing import Type

from digital_twin.config.app_config import DEFAULT_VECTOR_STORE
from digital_twin.vectordb.interface import VectorDB
from digital_twin.vectordb.qdrant.store import QdrantVectorDB


def get_selected_datastore_cls(
    vector_db_type: str = DEFAULT_VECTOR_STORE,
) -> Type[VectorDB]:
    """Returns the selected Datastore cls. Only one datastore
    should be selected for a specific deployment."""
    if vector_db_type == "qdrant":
        return QdrantVectorDB
    else:
        raise ValueError(f"Invalid Vector DB setting: {vector_db_type}")


def create_datastore(
    collection: str, vector_db_type: str = DEFAULT_VECTOR_STORE
) -> VectorDB:
    if vector_db_type == "qdrant":
        return QdrantVectorDB(collection=collection)
    else:
        raise ValueError(f"Invalid Vector DB setting: {vector_db_type}")