from typing import List, Optional
from fastapi import HTTPException
from postgrest import APIResponse

from digital_twin.config.constants import DocumentSource
from digital_twin.db.model import Connector, Credential, IndexAttempt
from digital_twin.server.model import ConnectorBase
from digital_twin.db.connectors.credentials import fetch_credential_by_id
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()

@log_supabase_api_error(logger)
def fetch_connectors(
    sources: Optional[List[str]] = None,
    input_types: Optional[List[str]] = None,
    disabled_status: Optional[bool] = None,
) -> List[Connector]:
    supabase = get_supabase_client()
    query = supabase.table("connector").select("*")
    if sources is not None:
        query = query.in_("source", sources)
    if input_types is not None:
        query = query.in_("input_type", input_types)
    if disabled_status is not None:
        query = query.eq("disabled", disabled_status)
    response: APIResponse = query.execute()
    return [Connector(**item) for item in response.data] if response.data else []


@log_supabase_api_error(logger)
def connector_by_name_exists(connector_name: str) -> bool:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table("connector").select(
        "*").eq("name", connector_name).execute()
    return bool(response.data)


@log_supabase_api_error(logger)
def fetch_connector_by_id(connector_id: int) -> Optional[Connector]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.table("connector").select(
        "*").eq("id", connector_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def create_connector(connector_data: ConnectorBase) -> Optional[Connector]:
    supabase = get_supabase_client()
    if connector_by_name_exists(connector_data.name):
        raise ValueError(
            "Connector by this name already exists, duplicate naming not allowed.")
    response = supabase.table("connector").insert(
        connector_data.dict()).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def update_connector(connector_id: int, connector_data: Connector) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id)
    if not connector:
        return None
    if connector_data.name != connector.name and connector_by_name_exists(connector_data.name):
        raise ValueError(
            "Connector by this name already exists, duplicate naming not allowed.")
    response = supabase.table("connector").update(
        connector_data.dict()).eq("id", connector_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def disable_connector(connector_id: int) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id)
    if not connector:
        return None
    response = supabase.table("connector").update(
        {"disabled": True}).eq("id", connector_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def delete_connector(connector_id: int) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id)
    if not connector:
        return None
    response = supabase.table("connector").delete().eq(
        "id", connector_id).execute()
    data = response.data
    return Connector(**data[0]) if data else None


@log_supabase_api_error(logger)
def get_connector_credentials(connector_id: int) -> List[Credential]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id)
    if not connector.data:
        raise ValueError(f"Connector by id {connector_id} does not exist")
    response: APIResponse = supabase.table("connector_credential_association").select(
        "credential(*)").eq("connector_id", connector_id).execute()
    
    return [Credential(**item['credential']) for item in response.data] if response.data else []

@log_supabase_api_error(logger)
def add_credential_to_connector(
    connector_id: int,
    credential_id: int,
    user_id: str
) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id)
    credential = fetch_credential_by_id(credential_id, user_id)

    if not connector:
        logger.error(
            f"Failed to add credentials to connector: Connector by id {connector_id} does not exist")
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if not credential:
        logger.error(
            f"Failed to add credentails to connector: credentials does not exist or does not belong to user {user_id}")
        raise HTTPException(
            status_code=401,
            detail="Credential does not exist or does not belong to user",
        )

    existing_association = supabase.table("connector_credential_association").select(
        "*").eq("connector_id", connector_id).eq("credential_id", credential_id).execute()
    if existing_association.data:
        return None
    association = {"connector_id": connector_id,
                   "credential_id": credential_id}
    supabase.table("connector_credential_association").insert(
        association).execute()

    return connector


@log_supabase_api_error(logger)
def remove_credential_from_connector(
    connector_id: int,
    credential_id: int,
    user_id: str
) -> Optional[Connector]:
    supabase = get_supabase_client()

    connector = fetch_connector_by_id(connector_id)
    credential = fetch_credential_by_id(credential_id, user_id)

    if not connector:
        logger.error(
            f"Failed to remove credentials for connector: Connector by id {connector_id} does not exist")
        raise HTTPException(status_code=404, detail="Connector does not exist")

    if not credential:
        logger.error(
            f"Failed to remove credentails for connector: credentials for {connector_id} does not exist or does not belong to user {user_id}")
        raise HTTPException(
            status_code=404,
            detail="Credential does not exist or does not belong to user",
        )

    response: APIResponse = supabase.table("connector_credential_association").select(
        "*").eq("connector_id", connector_id).eq("credential_id", credential_id).execute()

    if response.data:
        supabase.table("connector_credential_association").delete().eq(
            "connector_id", connector_id).eq("credential_id", credential_id).execute()
        return connector

    return None


@log_supabase_api_error(logger)
def fetch_latest_index_attempts_by_status() -> List[IndexAttempt]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.rpc("fetch_latest_index_attempt_by_connector",  params={}).execute()
    return [IndexAttempt(**item) for item in response.data]

def fetch_latest_index_attempt_by_connector(
    source: Optional[DocumentSource] = None,
) -> List[IndexAttempt]:
    supabase = get_supabase_client()
    latest_index_attempts: List[IndexAttempt] = []

    if source:
        connectors = fetch_connectors(
            sources=[source], disabled_status=False
        )
    else:
        connectors = fetch_connectors(disabled_status=False)

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
def fetch_latest_index_attempts_by_status() -> List[IndexAttempt]:
    supabase = get_supabase_client()
    response: APIResponse = supabase.rpc("fetch_latest_index_attempt_by_connector",  params={}).execute()
    return [IndexAttempt(**item) for item in response.data] if response.data else []

    
