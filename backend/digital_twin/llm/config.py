from typing import Union
from pydantic import BaseModel
from postgrest.exceptions import APIError

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger
from digital_twin.db.llm import log_api_error


class ApiKey(BaseModel):
    key_type: str
    key_value: str    
    
@log_api_error
def execute_single_item_query(table_name: str, query_params: dict) -> dict:
    client = get_supabase_client()
    query = client.table(table_name).select('*')
    for key, value in query_params.items():
        if value is not None:
            query = query.eq(key, value)
    response = query.single().execute()
    return response.data if response.data else None

@log_api_error
def execute_multi_item_query(table_name: str, query_params: dict) -> list:
    client = get_supabase_client()
    query = client.table(table_name).select('*')
    for key, value in query_params.items():
        if value is not None:
            query = query.eq(key, value)
    response = query.execute()
    return response.data[0] if response.data else None



data = execute_single_item_query('api_keys', {'user_id': user_id, 'key_type': key_type})

data = execute_multi_item_query('api_keys', {'user_id': user_id, 'key_type': key_type, 'key_value': new_key_value})
