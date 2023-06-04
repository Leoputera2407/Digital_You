from collections import defaultdict
from typing import cast
from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query

from digital_twin.config.constants import DocumentSource
from digital_twin.db.model import IndexAttempt, IndexingStatus


from digital_twin.server.model import (
    ApiKey,
    AuthStatus,
    AuthUrl,
    ConnectorBase,
    ConnectorIndexingStatus,
    ConnectorSnapshot,
    CredentialBase,
    CredentialSnapshot,
    GDriveCallback,
    GoogleAppCredentials,
    IndexAttemptSnapshot,
    ObjectCreationIdResponse,
    RunConnectorRequest,
    StatusResponse,
)

from digital_twin.connectors.google_drive.connector_auth import (
    DB_CREDENTIALS_DICT_KEY,
    get_auth_url,
    get_drive_tokens,
    get_google_app_cred,
    update_credential_access_tokens,
    upsert_google_app_cred,
    verify_csrf,
)
from digital_twin.db.connectors.connectors import (
    create_connector,
    delete_connector,
    update_connector,
    fetch_connector_by_id,
    fetch_connectors,
    fetch_latest_index_attempt_by_connector,
    fetch_latest_index_attempts_by_status,
    get_connector_credentials,
    add_credential_to_connector,
    remove_credential_from_connector,    
)
from digital_twin.db.connectors.credentials import (
    create_credential,
    delete_credential,
    update_credential,
    fetch_credential_by_id,
    fetch_credentials_for_user,
)
from digital_twin.db.connectors.index_attempt import create_index_attempt
from digital_twin.db.llm import (
    upsert_api_key,
    get_db_api_key,
    delete_api_key,
    upsert_model_config,
    get_model_config_by_user,
)
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.api_key import check_api_key_is_valid
from digital_twin.utils.auth_bearer import JWTBearer

router = APIRouter(prefix="/connector", dependencies=[Depends(JWTBearer())])

logger = setup_logger()


@router.get("/google-drive/app-credential")
def check_google_app_credentials_exist() -> dict[str, str]:
    try:
        # TODO: Create google app cred SQL
        cred = get_google_app_cred()
        return {"client_id"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Google App Credentials not found")


@router.put("/google-drive/app-credential")
def update_google_app_credentials(
    app_credentials: GoogleAppCredentials,
) -> StatusResponse:
    try:
        # TODO: Create google app cred SQL
        upsert_google_app_cred(app_credentials)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StatusResponse(
        success=True, message="Successfully saved Google App Credentials"
    )


@router.get("/google-drive/check-auth/{credential_id}")
def check_drive_tokens(
    credential_id: int,
) -> AuthStatus:
    db_credentials = fetch_credential_by_id(credential_id)
    if (
        not db_credentials
        or DB_CREDENTIALS_DICT_KEY not in db_credentials.credential_json
    ):
        return AuthStatus(authenticated=False)
    token_json_str = str(db_credentials.credential_json[DB_CREDENTIALS_DICT_KEY])
    google_drive_creds = get_drive_tokens(token_json_str=token_json_str)
    if google_drive_creds is None:
        return AuthStatus(authenticated=False)
    return AuthStatus(authenticated=True)


_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME = "google_drive_credential_id"


@router.get("/google-drive/authorize/{credential_id}", response_model=AuthUrl)
def google_drive_auth(
    response: Response, credential_id: str
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        httponly=True,
        max_age=600,
    )
    return AuthUrl(auth_url=get_auth_url(int(credential_id)))


@router.get("/google-drive/callback")
def google_drive_callback(
    request: Request,
    supabase_user_id: str, 
    callback: GDriveCallback = Depends(),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    credential_id = int(credential_id_cookie)
    verify_csrf(credential_id, callback.state)
    if (
        update_credential_access_tokens(callback.code, credential_id, supabase_user_id)
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Google Drive access tokens"
        )

    return StatusResponse(success=True, message="Updated Google Drive access tokens")


@router.get("/latest-index-attempt", response_model=list[IndexAttemptSnapshot])
def list_all_index_attempts(
) -> list[IndexAttemptSnapshot]:
    index_attempts = fetch_latest_index_attempt_by_connector()
    return [
        IndexAttemptSnapshot(
            source=index_attempt.connector.source,
            input_type=index_attempt.connector.input_type,
            status=index_attempt.status,
            connector_specific_config=index_attempt.connector.connector_specific_config,
            docs_indexed=0
            if not index_attempt.document_ids
            else len(index_attempt.document_ids),
            time_created=index_attempt.time_created,
            time_updated=index_attempt.time_updated,
        )
        for index_attempt in index_attempts
    ]


@router.get("/latest-index-attempt/{source}", response_model=list[IndexAttemptSnapshot])
def list_index_attempts(
    source: DocumentSource,
) -> list[IndexAttemptSnapshot]:
    index_attempts = fetch_latest_index_attempt_by_connector(source=source)
    return [
        IndexAttemptSnapshot(
            source=index_attempt.connector.source,
            input_type=index_attempt.connector.input_type,
            status=index_attempt.status,
            connector_specific_config=index_attempt.connector.connector_specific_config,
            docs_indexed=0
            if not index_attempt.document_ids
            else len(index_attempt.document_ids),
            time_created=index_attempt.time_created,
            time_updated=index_attempt.time_updated,
        )
        for index_attempt in index_attempts
    ]


@router.get("/list", response_model=list[ConnectorSnapshot], )
def get_connectors() -> list[ConnectorSnapshot]:
    connectors = fetch_connectors()
    return [
        ConnectorSnapshot.from_connector_db_model(connector) for connector in connectors
    ]


@router.get("/indexing-status")
def get_connector_indexing_status() -> list[ConnectorIndexingStatus]:
    connector_id_to_connector = {
        connector.id: connector for connector in fetch_connectors()
    }
    index_attempts = fetch_latest_index_attempts_by_status()
    connector_to_index_attempts: dict[int, list[IndexAttempt]] = defaultdict(list)
    for index_attempt in index_attempts:
        # don't consider index attempts where the connector has been deleted
        if index_attempt.connector_id:
            connector_to_index_attempts[index_attempt.connector_id].append(
                index_attempt
            )

    indexing_statuses: list[ConnectorIndexingStatus] = []
    for connector_id, index_attempts in connector_to_index_attempts.items():
        # NOTE: index_attempts is guaranteed to be length > 0
        connector = connector_id_to_connector[connector_id]
        index_attempts_sorted = sorted(
            index_attempts, key=lambda x: x.time_updated, reverse=True
        )
        successful_index_attempts_sorted = [
            index_attempt
            for index_attempt in index_attempts_sorted
            if index_attempt.status == IndexingStatus.SUCCESS
        ]
        indexing_statuses.append(
            ConnectorIndexingStatus(
                connector=ConnectorSnapshot.from_connector_db_model(connector),
                last_status=index_attempts_sorted[0].status,
                last_success=successful_index_attempts_sorted[0].time_updated
                if successful_index_attempts_sorted
                else None,
                docs_indexed=len(successful_index_attempts_sorted[0].document_ids)
                if successful_index_attempts_sorted
                and successful_index_attempts_sorted[0].document_ids
                else 0,
            ),
        )

    # add in the connector that haven't started indexing yet
    for connector in connector_id_to_connector.values():
        if connector.id not in connector_to_index_attempts:
            indexing_statuses.append(
                ConnectorIndexingStatus(
                    connector=ConnectorSnapshot.from_connector_db_model(connector),
                    last_status=IndexingStatus.NOT_STARTED,
                    last_success=None,
                    docs_indexed=0,
                ),
            )

    return indexing_statuses


@router.get(
    "/{connector_id}",
    response_model=ConnectorSnapshot | StatusResponse[int],
)
def get_connector_by_id(
    connector_id: int
) -> ConnectorSnapshot | StatusResponse[int]:
    connector = fetch_connector_by_id(connector_id)
    if connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    return ConnectorSnapshot.from_connector_db_model(connector)


@router.post("/create", response_model=ObjectCreationIdResponse)
def create_connector_from_model(
    connector_info: ConnectorBase,
) -> ObjectCreationIdResponse:
    try:
        return create_connector(connector_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{connector_id}",
    response_model=ConnectorSnapshot | StatusResponse[int],
)
def update_connector_from_model(
    connector_id: int,
    connector_data: ConnectorBase,
) -> ConnectorSnapshot | StatusResponse[int]:
    updated_connector = update_connector(connector_id, connector_data)
    if updated_connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    return ConnectorSnapshot.from_connector_db_model(updated_connector)


@router.delete("/{connector_id}", response_model=StatusResponse[int])
def delete_connector_by_id(
    connector_id: int
) -> StatusResponse[int]:
    return delete_connector(connector_id)


@router.get("/credential", response_model=list[CredentialSnapshot])
def get_credentials(
    supabase_user_id: str = Query(...)
) -> list[CredentialSnapshot]:
    credentials = fetch_credentials_for_user(supabase_user_id)
    return [
        CredentialSnapshot(
            id=credential.id,
            credential_json= credential.credential_json,
            user_id=credential.user_id,
            public_doc=credential.public_doc,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
        )
        for credential in credentials
    ]


@router.get(
    "/credential/{credential_id}",
    response_model=CredentialSnapshot | StatusResponse[int],
)
def get_credential_by_id(
    credential_id: int,
    supabase_user_id: str,
) -> CredentialSnapshot | StatusResponse[int]:
    credential = fetch_credential_by_id(credential_id, supabase_user_id)
    if credential is None:
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )

    return CredentialSnapshot(
        id=credential.id,
        credential_json=credential.credential_json,
        user_id=credential.user_id,
        public_doc=credential.public_doc,
        created_at=credential.created_at,
        created_at=credential.created_at,
    )


@router.post("/credential", response_model=ObjectCreationIdResponse)
def create_credential_from_model(
    connector_info: CredentialBase,
    supabase_user_id: str,
) -> ObjectCreationIdResponse:
    return create_credential(connector_info, supabase_user_id)


@router.patch(
    "/credential/{credential_id}",
    response_model=CredentialSnapshot | StatusResponse[int],
)
def update_credential_from_model(
    credential_id: int,
    credential_data: CredentialBase,
    supabase_user_id: str = Query(...),
) -> CredentialSnapshot | StatusResponse[int]:
    updated_credential = update_credential(
        credential_id, credential_data, supabase_user_id
    )
    if updated_credential is None:
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )

    return CredentialSnapshot(
        id=updated_credential.id,
        credential_json=updated_credential.credential_json,
        user_id=updated_credential.user_id,
        public_doc=updated_credential.public_doc,
        created_at=updated_credential.created_at,
        updated_at=updated_credential.updated_at,
    )


@router.delete("/credential/{credential_id}", response_model=StatusResponse[int])
def delete_credential_by_id(
    credential_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse:
    delete_credential(credential_id, supabase_user_id)
    return StatusResponse(
        success=True, message="Credential deleted successfully", data=credential_id
    )


@router.put("/{connector_id}/credential/{credential_id}")
def associate_credential_to_connector(
    connector_id: int,
    credential_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse[int]:
    return add_credential_to_connector(connector_id, credential_id, supabase_user_id)


@router.delete("/{connector_id}/credential/{credential_id}")
def dissociate_credential_from_connector(
    connector_id: int,
    credential_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse[int]:
    return remove_credential_from_connector(
        connector_id, credential_id, supabase_user_id
    )


@router.post("/run-once")
def connector_run_once(
    run_info: RunConnectorRequest,
    supabase_user_id: str = Query(...),
) -> StatusResponse[list[int]]:
    connector_id = run_info.connector_id
    specified_credential_ids = run_info.credential_ids
    try:
        possible_credentials = get_connector_credentials(
            run_info.connector_id
        )
        possible_credential_ids = [credential.id for credential in possible_credentials]
    except ValueError:
        return StatusResponse(
            success=False,
            message=f"Connector by id {connector_id} does not exist.",
        )

    if not specified_credential_ids:
        credential_ids = possible_credential_ids
    else:
        if set(specified_credential_ids).issubset(set(possible_credential_ids)):
            credential_ids = specified_credential_ids
        else:
            return StatusResponse(
                success=False,
                message=f"Not all specified credentials are associated with connector",
            )

    if not credential_ids:
        return StatusResponse(
            success=False,
            message=f"Connector has no valid credentials, cannot create index attempts.",
        )

    index_attempt_ids = [
        create_index_attempt(run_info.connector_id, credential_id)
        for credential_id in credential_ids
    ]
    return StatusResponse(
        success=True,
        message=f"Successfully created {len(index_attempt_ids)} index attempts",
        data=index_attempt_ids,
    )

"""
@router.head("/openai-api-key/validate")
def validate_existing_openai_api_key() -> None:
    try:
        openai_api_key = get_openai_api_key()
        is_valid = check_openai_api_key_is_valid(openai_api_key)
    except ConfigNotFoundError:
        raise HTTPException(status_code=404, detail="Key not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid API key provided")


@router.get("/openai-api-key", response_model=ApiKey)
def get_openai_api_key_from_dynamic_config_store(
) -> ApiKey:
    """
    NOTE: Only gets value from dynamic config store as to not expose env variables.
    """
    try:
        # only get last 4 characters of key to not expose full key
        return ApiKey(
            api_key=cast(
                str, get_dynamic_config_store().load(OPENAI_API_KEY_STORAGE_KEY)
            )[-4:]
        )
    except ConfigNotFoundError:
        raise HTTPException(status_code=404, detail="Key not found")


@router.post("/openai-api-key")
def store_openai_api_key(
    request: ApiKey,
) -> None:
    try:
        is_valid = check_openai_api_key_is_valid(request.api_key)
        if not is_valid:
            raise HTTPException(400, "Invalid API key provided")
        get_dynamic_config_store().store(OPENAI_API_KEY_STORAGE_KEY, request.api_key)
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@router.delete("/openai-api-key")
def delete_openai_api_key(
) -> None:
    get_dynamic_config_store().delete(OPENAI_API_KEY_STORAGE_KEY)
""""