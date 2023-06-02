from typing import Union
from pydantic import BaseModel
from postgrest.exceptions import APIError

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

class ApiKey(BaseModel):
    key_type: str
    key_value: str

def get_api_key(user_id: str, key_type: str) -> Union[ApiKey, None]:
    try:
        response = get_supabase_client().table('api_keys').select('key_type', 'key_value').eq('user_id', user_id).eq('key_type', key_type).single().execute()
    except APIError as e:
        logger.error(f'Error retrieving API key for user {user_id} and key type {key_type}: {e}')
        return ApiKey(key_type="openai_api_key", key_value=OPENAI_API_KEY) if OPENAI_API_KEY != "" else None 
    
    return ApiKey(**response.data)

def update_api_key(user_id: str, key_type: str, new_key_value: str) -> bool:
    if not check_api_key_is_valid(new_key_value, key_type):
        return False
    try:
        get_supabase_client().table('api_keys').update({'key_value': new_key_value}).eq('user_id', user_id).eq('key_type', key_type).execute()
    except APIError as e:
        logger.error(f'Error updating API key for user {user_id} and key type {key_type}: {e}')
        return False
    else:
        return True