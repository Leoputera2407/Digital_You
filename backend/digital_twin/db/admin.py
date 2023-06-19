from datetime import datetime
from typing import Optional
from postgrest import APIResponse

from digital_twin.utils.clients import get_supabase_client


def get_db_current_time() -> Optional[datetime]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.rpc('get_db_time', {}).execute()
    return response.data[0]['ts'] if response.data else None