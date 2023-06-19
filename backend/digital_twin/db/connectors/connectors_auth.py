from typing import Optional
from postgrest import APIResponse

from digital_twin.db.model import DBCSRFToken
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()

@log_supabase_api_error(logger)
def store_csrf(credential_id: int, csrf: str) -> Optional[DBCSRFToken]:
    supabase = get_supabase_client()
    payload = {
        'credential_id': credential_id,
        'csrf_token': csrf
    }
    response: APIResponse = supabase.table('google_csrf_tokens').upsert(payload, on_conflict="credential_id").execute()
    return DBCSRFToken(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def consume_csrf(credential_id: int) -> Optional[DBCSRFToken]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table('google_csrf_tokens').select('csrf_token').eq('credential_id', credential_id).execute()
    if response.data:
        csrf_token = response.data[0]['csrf_token']
        response = supabase.table('csrf_tokens').delete().eq('credential_id', credential_id).eq("csrf_token", csrf_token).execute()
        if not response.data:
            raise Exception('Failed to consume CSRF token')
        return DBCSRFToken(**response.data[0])
    else:
        return None