import json
from typing import Optional
from postgrest import APIResponse

from digital_twin.db.model import DBGoogleAppCredential
from digital_twin.server.model import GoogleAppCredentials
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()

@log_supabase_api_error(logger)
def fetch_db_google_app_creds() -> Optional[DBGoogleAppCredential]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table('google_app_credentials').select('*').execute()
    return DBGoogleAppCredential(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def upsert_db_google_app_cred(app_credentials: GoogleAppCredentials) -> Optional[DBGoogleAppCredential]:
    supabase = get_supabase_client()
    payload = {
        'credentials_json': json.dumps(app_credentials)
    }
    response: APIResponse = supabase.table('google_app_credentials').upsert(
        payload, on_conflict="credentials_json").execute()
    print(response.data)
    return DBGoogleAppCredential(**response.data[0]) if response.data else None


