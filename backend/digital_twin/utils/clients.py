import typesense  # type: ignore
from qdrant_client import QdrantClient

from digital_twin.config.app_config import (
    QDRANT_API_KEY,
    QDRANT_URL,
    QDRANT_PORT,
    QDRANT_HOST,
    TYPESENSE_API_KEY,
    TYPESENSE_HOST,
    TYPESENSE_PORT,
    TYPESENSE_PROTOCOL,
)

_qdrant_client: QdrantClient | None = None
_typesense_client: typesense.Client | None = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        if QDRANT_URL and QDRANT_API_KEY:
            _qdrant_client = QdrantClient(
                url=QDRANT_URL, api_key=QDRANT_API_KEY
            )
        elif QDRANT_HOST and QDRANT_PORT:
            _qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        else:
            raise Exception("Unable to instantiate QdrantClient")
 
    return _qdrant_client



def get_typesense_client() -> typesense.Client:
    global _typesense_client
    if _typesense_client is None:
        if TYPESENSE_HOST and TYPESENSE_PORT and TYPESENSE_API_KEY and TYPESENSE_PROTOCOL:
            _typesense_client = typesense.Client(
                {
                    "api_key": TYPESENSE_API_KEY,
                    "nodes": [
                        {
                            "host": TYPESENSE_HOST,
                            "port": str(TYPESENSE_PORT),
                            "protocol": str(TYPESENSE_PROTOCOL),
                        }
                    ],
                }
            )
        else:
            raise Exception("Unable to instantiate TypesenseClient")

    return _typesense_client
