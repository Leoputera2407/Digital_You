from typing import List, Optional

from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error
from digital_twin.db.model import APIKey, ModelConfig, DBAPIKeyType
from digital_twin.server.model import APIKeyBase, BaseModelConfig

logger = setup_logger()

def mask_api_key(sensitive_str: str) -> str:
    return sensitive_str[:4] + "***...***" + sensitive_str[-4:]

@log_supabase_api_error(logger)
def upsert_api_key(user_id: str, api_key: APIKeyBase) -> Optional[APIKey]:
    supabase = get_supabase_client()
    payload = {
        "user_id": user_id,
        **api_key.dict()
    }
    response = supabase.table("api_keys").upsert(payload, on_conflict="user_id,key_type").execute()
    data = response.data
    return APIKey(**data[0]) if data else None


@log_supabase_api_error(logger)
def get_db_api_key(user_id: str = None, key_type: DBAPIKeyType = None) -> List[APIKey]:
    supabase = get_supabase_client()
    if not user_id and not key_type:
        return None
    query = supabase.table("api_keys").select("*")
    if user_id:
        query = query.eq("user_id", user_id)
    if key_type:
        query = query.eq("key_type", key_type)
    response = query.execute()
    data = response.data
    return [APIKey(**api_key) for api_key in data] if data else []


@log_supabase_api_error(logger)
def delete_api_key(user_id: str, key_type: DBAPIKeyType) -> Optional[APIKey]:
    supabase = get_supabase_client()
    response = supabase.table("api_keys").delete().eq(
        "key_type", key_type).eq("user_id", user_id).execute()
    data = response.data
    return APIKey(**data[0]) if data else None


@log_supabase_api_error(logger)
def upsert_model_config(user_id: str, model_config: BaseModelConfig) -> Optional[ModelConfig]:
    supabase = get_supabase_client()
    payload = {
        "user_id": user_id,
        **model_config.dict()
    }
    response = supabase.table("model_config").upsert(payload, on_conflict="user_id").execute()
    data = response.data
    return ModelConfig(**data[0]) if data else None


@log_supabase_api_error(logger)
def get_model_config_by_user(user_id: str) -> Optional[ModelConfig]:
    supabase = get_supabase_client()
    response = supabase.table("model_config").select(
        "*").eq("user_id", user_id).single().execute()
    data = response.data
    return ModelConfig(**data) if data else None

# This mostly for testing purposes, don't expose to the API
@log_supabase_api_error(logger)
def delete_model_config(user_id: str, model_id: str) -> Optional[ModelConfig]:
    supabase = get_supabase_client()
    response = supabase.table("model_config").delete().eq(
        "model_id", model_id).eq("user_id", user_id).execute()
    data = response.data
    return ModelConfig(**data[0]) if data else None

@log_supabase_api_error(logger)
def single_item_query(table_name, query_params) -> Optional[ModelConfig]:
    client = get_supabase_client()
    query = client.table(table_name).select('*')
    for key, value in query_params.items():
        if value is not None:
            query = query.eq(key, value)
    response = query.single().execute()
    data = response.data
    return ModelConfig(**data[0]) if response.data else None

@log_supabase_api_error(logger)
def multi_item_query(table_name, query_params) -> List[ModelConfig]:
    client = get_supabase_client()
    query = client.table(table_name).select('*')
    for key, value in query_params.items():
        if value is not None:
            query = query.eq(key, value)
    response = query.execute()
    data = response.data
    return[ModelConfig(**i) for i in data] if data else None