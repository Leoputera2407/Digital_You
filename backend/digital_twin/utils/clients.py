from typing import Any, Optional
from qdrant_client import QdrantClient
from supabase import create_client, Client

from digital_twin.config.app_config import (
    QDRANT_API_KEY,
    QDRANT_URL,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)

_qdrant_client: QdrantClient | None = None
_supabase_client: Client | None = None


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        if QDRANT_URL and QDRANT_API_KEY:
            _qdrant_client = QdrantClient(
                url=QDRANT_URL, api_key=QDRANT_API_KEY
            )
        else:
            raise Exception("Unable to instantiate QdrantClient")
 
    return _qdrant_client


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            _supabase_client = create_client(
                SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        else:
            raise Exception("Unable to instantiate SupabaseClient")
        
    return _supabase_client
