from typing import Optional

from fastapi import HTTPException
from postgrest import APIResponse

from digital_twin.db.connectors.connectors import fetch_connector_by_id
from digital_twin.db.connectors.credentials import fetch_credential_by_id
from digital_twin.db.model import IndexingStatus, Connector, ConnectorCredentialAssociation
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()


@log_supabase_api_error(logger)
def get_all_connector_credential_associations() -> list[ConnectorCredentialAssociation]:
    supabase = get_supabase_client()
    query = supabase.table("connector_credential_association").select("*").execute()
    return [ConnectorCredentialAssociation(**item) for item in query.data] if query.data else []

@log_supabase_api_error(logger)
def get_connector_credential_assocation(
    connector_id: int,
    credential_id: int,
) -> Optional[ConnectorCredentialAssociation]:
    supabase = get_supabase_client()
    query = supabase.table("connector_credential_association").select("*").eq("connector_id", connector_id).eq("credential_id", credential_id).execute()
    return ConnectorCredentialAssociation(**query.data[0]) if query.data else None


@log_supabase_api_error(logger)
def add_credential_to_connector(    
    user_id: str,
    connector_id: int,
    credential_id: int,
) -> Optional[Connector]:
    supabase = get_supabase_client()
    connector = fetch_connector_by_id(connector_id, user_id)
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
    user_id: str,
    connector_id: int,
    credential_id: int,
) -> Optional[Connector]:
    supabase = get_supabase_client()

    connector = fetch_connector_by_id(connector_id, user_id)
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