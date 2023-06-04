from typing import List, Optional

from postgrest import APIResponse
from digital_twin.db.model import Credential
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()

@log_supabase_api_error(logger)
def fetch_credentials_for_user(user_id: str) -> Optional[List[Credential]]:
    supabase = get_supabase_client()
    if user_id:
        response: APIResponse = supabase.table("credential").select('*').eq('user_id', user_id).execute()
    else:
        return None
    return [Credential(**credential) for credential in response.data] if response.data else None

@log_supabase_api_error(logger)
def fetch_credential_by_id(credential_id: int, user_id: Optional[str] = None) -> Optional[Credential]:
    supabase = get_supabase_client()
    query = supabase.table("credential").select('*').eq('id', credential_id)
    if user_id:
        query = query.eq('user_id', user_id)
    response: APIResponse = query.single().execute()

    return Credential(**response.data) if response.data else None

@log_supabase_api_error(logger)
def create_credential(credential_data: dict, user_id: Optional[str] = None) -> Optional[Credential]:
    supabase = get_supabase_client()
    credential = {
        'credential_json': credential_data['credential_json'],
        'user_id': user_id if user_id else None,
        'public_doc': credential_data['public_doc'],
    }
    response: APIResponse = supabase.table("credential").insert(credential).execute()
    return Credential(**response.data[0]) if response.data else None

@log_supabase_api_error(logger)
def update_credential(credential_id: int, credential_data: dict, user_id: Optional[str] = None) -> Optional[Credential]:
    supabase = get_supabase_client()
    credential = fetch_credential_by_id(credential_id, user_id)
    if not credential:
        return None

    updated_credential = {
        'credential_json': credential_data['credential_json'],
        'user_id': user_id if user_id else None,
        'public_doc': credential_data['public_doc'],
    }
    query = supabase.table("credential").update(updated_credential).eq('id', credential_id)
    if user_id:
      query = query.eq('user_id', user_id)
    
    response: APIResponse = query.execute()
    return Credential(**response.data[0]) if response.data else None

@log_supabase_api_error(logger)
def delete_credential(credential_id: int, user_id: Optional[str] = None) -> Optional[Credential]:
    supabase = get_supabase_client()
    credential = fetch_credential_by_id(credential_id, user_id)
    if not credential:
        return None
    
    response: APIResponse = supabase.table("credential").delete().eq('id', credential_id).execute()
    return Credential(**response.data[0]) if response.data else None