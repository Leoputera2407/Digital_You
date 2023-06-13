from typing import Union
from pydantic import BaseModel
from postgrest.exceptions import APIError

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.logging import setup_logger
from digital_twin.db.llm import single_item_query, multi_item_query


class ApiKey(BaseModel):
    key_type: str
    key_value: str    
    

def execute_single_item_query(table_name: str, query_params: dict) -> dict:
    return single_item_query(table_name, query_params)


def execute_multi_item_query(table_name: str, query_params: dict) -> list:
    return multi_item_query(table_name, query_params) 


data = execute_single_item_query('api_keys', {'user_id': user_id, 'key_type': key_type})

data = execute_multi_item_query('api_keys', {'user_id': user_id, 'key_type': key_type, 'key_value': new_key_value})
