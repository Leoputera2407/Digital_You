from typing import Optional, List

from postgrest import APIResponse
from digital_twin.db.model import IndexAttempt
from digital_twin.db.connectors.connectors import get_connector_credentials
from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error

logger = setup_logger()


@log_supabase_api_error(logger)
def create_index_attempt(connector_id: int, credential_id: int, user_id: Optional[str] = None ) -> Optional[IndexAttempt]:
    client = get_supabase_client()
    credential_result = get_connector_credentials(
        user_id=user_id, connector_id=connector_id, credential_id=credential_id
    )
    if not credential_result:
        logger.error(
            f'Cannot Index as credential {credential_id} is not assocaited with connector {connector_id} for {user_id}')
        raise ValueError(
            f'Cannot Index as credential is not assocaited with connector')

    data = {
        'connector_id': connector_id,
        'credential_id': credential_id,
        'status': 'not_started'
    }
    response: APIResponse = client.table(
        'index_attempt').insert(data).execute()
    return IndexAttempt(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def get_inprogress_index_attempts(connector_id: Optional[int] = None) -> List[IndexAttempt]:
    client = get_supabase_client()
    query = client.table('index_attempt').select('*')
    if connector_id is not None:
        query = query.eq('connector_id', connector_id)
    query = query.eq('status', 'in_progress')
    response: APIResponse = query.execute()
    return [IndexAttempt(**item) for item in response.data] if response.data else []

@log_supabase_api_error(logger)
def get_not_started_index_attempts(connector_id: Optional[int] = None) -> List[IndexAttempt]:
    client = get_supabase_client()
    query = client.table('index_attempt').select('*')
    if connector_id is not None:
        query = query.eq('connector_id', connector_id)
    query = query.eq('status', 'not_started')
    response: APIResponse = query.execute()
    return [IndexAttempt(**item) for item in response.data] if response.data else []


@log_supabase_api_error(logger)
def get_not_started_index_attempts() -> List[IndexAttempt]:
    client = get_supabase_client()
    query = client.table('index_attempt').select(
        '*').eq('status', 'not_started')
    response: APIResponse = query.execute()
    return [IndexAttempt(**item) for item in response.data] if response.data else []


@log_supabase_api_error(logger)
def mark_attempt_in_progress(index_attempt_id: int) -> Optional[IndexAttempt]:
    client = get_supabase_client()
    data = {'status': 'in_progress'}
    response: APIResponse = client.table('index_attempt').update(
        data).eq('id', index_attempt_id).execute()
    return IndexAttempt(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def mark_attempt_succeeded(index_attempt_id: int, docs_indexed: list[str]) -> Optional[IndexAttempt]:
    client = get_supabase_client()
    data = {
        'status': 'success',
        'document_ids': docs_indexed
    }
    response: APIResponse = client.table('index_attempt').update(
        data).eq('id', index_attempt_id).execute()
    return IndexAttempt(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def mark_attempt_failed(index_attempt_id: int, failure_reason: str = "Unknown") -> Optional[IndexAttempt]:
    client = get_supabase_client()
    data = {
        'status': 'failed',
        'error_msg': failure_reason
    }
    response: APIResponse = client.table('index_attempt').update(
        data).eq('id', index_attempt_id).execute()
    return IndexAttempt(**response.data[0]) if response.data else None


@log_supabase_api_error(logger)
def get_last_finished_attempt(connector_id: int) -> Optional[IndexAttempt]:
    client = get_supabase_client()
    query = client.table('index_attempt').select(
        '*').eq('connector_id', connector_id).eq('status', 'success')
    response: APIResponse = query.order(
        'updated_at', desc=True).execute()
    return IndexAttempt(**response.data[0]) if response.data else None
