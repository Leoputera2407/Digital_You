from typing import Optional
from uuid import UUID

from digital_twin.db.model import User
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()


@log_supabase_api_error(logger)
def get_user_by_id(user_id: UUID) -> Optional[User]:
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    data = response.data
    return User(**data) if data else None

@log_supabase_api_error(logger)
def get_qdrant_collection_for_user(user_id: UUID) -> Optional[UUID]:
    user = get_user_by_id(user_id)
    return user.qdrant_collection_key if user else None
