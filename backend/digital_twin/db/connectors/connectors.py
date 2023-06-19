from typing import List, Optional
from postgrest import APIResponse

from digital_twin.config.constants import DocumentSource
from digital_twin.db.model import Connector, Credential, IndexAttempt
from digital_twin.server.model import ConnectorBase
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()

@log_supabase_api_error(logger)
def fetch_connectors(
    user_id: Optional[str] = None,
    sources: Optional[List[str]] = None,
    input_types: Optional[List[str]] = None,
    disabled_status: Optional[bool] = None,
) -> List[Connector]:
    supabase = get_supabase_client()
    query = supabase.table("connector").select("*")
    if user_id:
        query = query.eq("user_id", user_id)
    if sources is not None:
        query = query.in_("source", sources)
    if input_types is not None:
        query = query.in_("input_type", input_types)
    if disabled_status is not None:
        query = query.eq("disabled", disabled_status)
    response: APIResponse = query.execute()
    return [Connector(**item) for item in response.data] if response.data else []


@log_supabase_api_error(logger)
def connector_by_name_exists(user_id: str, connector_name: str) -> bool:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table("connector").select(
        "*").eq("name", connector_name).eq("user_id", user_id).execute()
    return bool(response.data)


@log_supabase_api_error(logger)
def fetch_connector_by_id(connector_id: int, user_id: Optional[str] = None ) -> Optional[Connector]:
    supabase = get_supabase_client()
    query = supabase.table("connector").select(
        "*").eq("id", connector_id)
    if user_id:
        query = query.eq("user_id", user_id)
    response: APIResponse = query.execute()
    data = response.data
    return Connector(**data[0]) if data else None

@log_supabase_api_error(logger)
def fetch_connector_by_list_of_id(user_id: str, connector_id_list: List[int]) -> List[Connector]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table("connector").select(
        "*").in_("id", connector_id_list).eq("user_id", user_id).execute()
    return [Connector(**item) for item in response.data] if response.data else [] 


@log_supabase_api_error(logger)
def create_connector(user_id: str, connector_data: ConnectorBase) -> Optional[Connector]:
    supabase = get_supabase_client()
    if connector_by_name_exists(user_id, connector_data.name):
        raise ValueError(
            "Connector by this name already exists, duplicate naming not allowed.")
    payload = {
        "user_id": user_id,
        **connector_data.dict()
    }
    
    response = supabase.table("connector").insert(payload).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def update_connector(user_id: str, connector_id: int, connector_data: Connector) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id, user_id)
    if not connector:
        return None
    if connector_data.name != connector.name and connector_by_name_exists(user_id, connector_data.name):
        raise ValueError(
            "Connector by this name already exists, duplicate naming not allowed.")
    response = supabase.table("connector").update(
        connector_data.dict()).eq("id", connector_id).eq("user_id", user_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def disable_connector(user_id: str, connector_id: int) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id, user_id)
    if not connector:
        return None
    response = supabase.table("connector").update(
        {"disabled": True}).eq("id", connector_id).eq("user_id", user_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def delete_connector(user_id:str, connector_id: int) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id, user_id)
    if not connector:
        return None
    response = supabase.table("connector").delete().eq(
        "id", connector_id).eq("user_id", user_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def get_connector_credentials(user_id: str, connector_id: int, credential_id: int = None) -> List[Credential]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id, user_id)
    if not connector:
        raise ValueError(f"Connector by id {connector_id} does not exist")
    query = supabase.table("connector_credential_association").select(
        "credential(*)").eq("connector_id", connector_id)
    if credential_id:
        query = query.eq("credential_id", credential_id)
    response: APIResponse = query.execute()
    return [Credential(**item['credential']) for item in response.data] if response.data else []




@log_supabase_api_error(logger)
def fetch_latest_index_attempts_by_status() -> List[IndexAttempt]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.rpc("fetch_latest_index_attempt_by_connector",  params={}).execute()
    return [IndexAttempt(**item) for item in response.data]

def fetch_latest_index_attempt_by_connector(
    user_id: str,
    source: Optional[DocumentSource] = None,
) -> List[IndexAttempt]:
    supabase = get_supabase_client()
    latest_index_attempts: List[IndexAttempt] = []

    if source:
        connectors = fetch_connectors(
            user_id=user_id, sources=[source], disabled_status=False
        )
    else:
        connectors = fetch_connectors(user_id=user_id, disabled_status=False)

    if not connectors:
        logger.info("No connectors found")
        return []

    for connector in connectors:
        response: APIResponse = supabase.table("index_attempt").select('*').eq(
            "connector_id", connector.id).order("updated_at", desc=True).execute()
        if response.data:
            latest_index_attempt = IndexAttempt(**response.data[0])
            latest_index_attempts.append(latest_index_attempt)

    return latest_index_attempts


@log_supabase_api_error(logger)
def fetch_latest_index_attempts_by_status(user_id: str) -> List[IndexAttempt]:
    supabase = get_supabase_client()
    # Will return the latest index attempt status for each connector and credential pair
    response: APIResponse = supabase.rpc("fetch_latest_index_attempt_by_connector",  params={"func_user_id": user_id}).execute()
    return [IndexAttempt(**item) for item in response.data] if response.data else []

    
