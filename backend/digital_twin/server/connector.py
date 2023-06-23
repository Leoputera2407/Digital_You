from collections import defaultdict
from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query
from typing import Optional

from digital_twin.config.app_config import IS_DEV
from digital_twin.config.constants import DocumentSource
from digital_twin.db.model import IndexAttempt, IndexingStatus


from digital_twin.server.model import (
    AuthStatus,
    AuthUrl,
    ConnectorBase,
    ConnectorIndexingStatus,
    ConnectorSnapshot,
    CredentialBase,
    CredentialSnapshot,
    GDriveCallback,
    NotionCallback,
    # GoogleAppWebCredentials,
    IndexAttemptSnapshot,
    ObjectCreationIdResponse,
    RunConnectorRequest,
    StatusResponse,
)
from digital_twin.db.model import (
    Connector, 
    Credential,
    User,
    UserRole,
)

from digital_twin.connectors.notion.connector_auth import (
    get_auth_url as get_notion_auth_url,
    update_credential_access_tokens as update_notion_credential_access_tokens,
)

from digital_twin.connectors.google_drive.connector_auth import (
    DB_CREDENTIALS_DICT_KEY,
    get_auth_url as get_gdrive_auth_url,
    get_drive_tokens,
    get_google_app_cred,
    update_credential_access_tokens as update_gdrive_credential_access_tokens,
    # upsert_google_app_cred,
    verify_csrf as verify_gdrive_csrf,
)
from digital_twin.db.connectors.connector_credential_association import (
    add_credential_to_connector,
    remove_credential_from_connector,
)
from digital_twin.db.connectors.connectors import (
    create_connector,
    delete_connector,
    update_connector,
    fetch_connector_by_id,
    fetch_connectors,
    fetch_latest_index_attempt_by_connector,
    fetch_latest_index_attempts_by_status,
)
from digital_twin.db.connectors.credentials import (
    create_credential,
    delete_credential,
    update_credential,
    fetch_credential_by_id,
    mask_credential_dict,
)
from digital_twin.db.connectors.index_attempt import create_index_attempt
from digital_twin.db.user import get_user_by_id
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.auth_bearer import JWTBearer

#router = APIRouter(prefix="/connector", dependencies=[Depends(JWTBearer())])
router = APIRouter(prefix="/connector")

logger = setup_logger()

@router.get("/google-drive/app-credential")
def check_google_app_credentials_exist() -> dict[str, str]:
    try:
        return {"client_id": get_google_app_cred().client_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Google App Credentials not found")

# TODO: Don't expose this methods below as we don't want people over-writing our app creds
# Maybe admin level makes sense later
"""
@router.put("/admin/google-drive/app-credential")
def update_google_app_credentials(
    app_credentials: GoogleAppWebCredentials,
) -> StatusResponse:
    try:
        upsert_google_app_cred(app_credentials.web)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StatusResponse(
        success=True, message="Successfully saved Google App Credentials"
    )
"""

@router.get("/google-drive/check-auth/{credential_id}")
def check_drive_tokens(
    credential_id: int,
) -> AuthStatus:
    db_credentials: Optional[Credential] = fetch_credential_by_id(credential_id)
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
    return AuthUrl(auth_url=get_gdrive_auth_url(int(credential_id)))


@router.get("/google-drive/callback")
def google_drive_callback(
    request: Request,
    supabase_user_id: str = Query(...), 
    callback: GDriveCallback = Depends(),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    credential_id = int(credential_id_cookie)
    verify_gdrive_csrf(credential_id, callback.state)
    if (
        update_gdrive_credential_access_tokens(callback.code, credential_id, supabase_user_id)
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Google Drive access tokens"
        )

    return StatusResponse(success=True, message="Updated Google Drive access tokens")


_NOTION_CREDENTIAL_ID_COOKIE_NAME = "notion_credential_id"

@router.get("/notion/authorize/{credential_id}", response_model=AuthUrl)
def notion_auth(
    response: Response, credential_id: str
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=_NOTION_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        httponly=True,
        max_age=600,
    )
    return AuthUrl(auth_url=get_notion_auth_url())

@router.get("/notion/callback")
def notion_callback(
    request: Request,
    supabase_user_id: str = Query(...), 
    callback: NotionCallback = Depends(),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_NOTION_CREDENTIAL_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    credential_id = int(credential_id_cookie)
    if (
        update_notion_credential_access_tokens(callback.code, credential_id, supabase_user_id)
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Notion access tokens"
        )

    return StatusResponse(success=True, message="Updated Notion access tokens")


"""
# TODO: Workaround, should remove on deployment
if IS_DEV:
    @router.get("/google-drive-non-prod/callback")
    def google_drive_callback_non_prod(
        supabase_user_id: str = Query(...), 
        callback: GDriveCallback = Depends(),
    ) -> StatusResponse:
        credentials = fetch_credentials_for_user(supabase_user_id)
        credential_with_empty_json = next((credential for credential in credentials if not credential.credential_json), None)
        if credential_with_empty_json is None:
            raise HTTPException(
                status_code=500, detail="Unable to fetch Google Drive access tokens"
            )
        if (
            update_gdrive_credential_access_tokens(callback.code, credential_with_empty_json.id, supabase_user_id)
            is None
        ):
            raise HTTPException(
                status_code=500, detail="Unable to fetch Google Drive access tokens"
            )

        return StatusResponse(success=True, message="Updated Google Drive access tokens")

    @router.get("/notion-non-prod/callback")
    def notion_callback_non_prod(
        supabase_user_id: str = Query(...), 
        callback: NotionCallback = Depends(),
    ) -> StatusResponse:
       from digital_twin.connectors.notion.connector_auth import  DB_CREDENTIALS_DICT_KEY
       credentials = fetch_credentials_for_user(supabase_user_id)
       credential_with_empty_json = next((credential for credential in credentials if not credential.credential_json), None)
       if credential_with_empty_json is None:
            raise HTTPException(
                status_code=500, detail="Unable to fetch Notion access tokens"
            )
       if (
            update_notion_credential_access_tokens(callback.code, credential_with_empty_json.id, supabase_user_id)
            is None
        ):
            raise HTTPException(
                status_code=500, detail="Unable to fetch Notion access tokens"
            )
       
       return StatusResponse(success=True, message="Updated Notion access tokens")



@router.get("/latest-index-attempt", response_model=list[IndexAttemptSnapshot])
def list_all_index_attempts(
    supabase_user_id: str = Query(...),
) -> list[IndexAttemptSnapshot]:
    index_attempts = fetch_latest_index_attempt_by_connector(supabase_user_id)
    connectors = fetch_connector_by_list_of_id(supabase_user_id, [index_attempt.connector_id for index_attempt in index_attempts])
    connectors_dict = {connector.id: connector for connector in connectors}
    index_attempt_connector_pair_list = [(index_attempt, connectors_dict.get(index_attempt.connector_id)) for index_attempt in index_attempts]

    return [
        IndexAttemptSnapshot(
            source=connector.source,
            input_type=connector.input_type,
            status=index_attempt.status,
            connector_specific_config=connector.connector_specific_config,
            docs_indexed=0 if not index_attempt.document_ids
                else len(index_attempt.document_ids),
            created_at=index_attempt.created_at,
            updated_at=index_attempt.updated_at,
        )
        for (index_attempt, connector) in index_attempt_connector_pair_list
    ]


@router.get("/latest-index-attempt/{source}", response_model=list[IndexAttemptSnapshot])
def list_index_attempts(
    source: DocumentSource,
    supabase_user_id: str = Query(...),
) -> list[IndexAttemptSnapshot]:
    index_attempts = fetch_latest_index_attempt_by_connector(supabase_user_id, source=source.value)
    if not index_attempts:
        return []
    connectors = fetch_connector_by_list_of_id(supabase_user_id, [index_attempt.connector_id for index_attempt in index_attempts])
    connectors_dict = {connector.id: connector for connector in connectors}
    index_attempt_connector_pair_list = [(index_attempt, connectors_dict.get(index_attempt.connector_id)) for index_attempt in index_attempts]

    return [
        IndexAttemptSnapshot(
            source=connector.source,
            input_type=connector.input_type,
            status=index_attempt.status,
            connector_specific_config=connector.connector_specific_config,
            docs_indexed=0 if not index_attempt.document_ids
                else len(index_attempt.document_ids),
            created_at=index_attempt.created_at,
            updated_at=index_attempt.updated_at,
        )
        for (index_attempt, connector) in index_attempt_connector_pair_list
    ]


@router.get("/indexing-status")
def get_connector_indexing_status(
    supabase_user_id: str = Query(...),
) -> list[ConnectorIndexingStatus]:
    connector_id_to_connector: dict[int, Connector] = {
        connector.id: connector for connector in fetch_connectors(
            user_id = supabase_user_id
        )
    }
    # Returns the latest status for each connector and credential pair
    index_attempts = fetch_latest_index_attempts_by_status(supabase_user_id)
    connector_credential_pair_to_index_attempts: dict[
            tuple[int, int], list[IndexAttempt]
        ] = defaultdict(list)
    for index_attempt in index_attempts:
        # don't consider index attempts where the connector has been deleted
        if (
            index_attempt.connector_id is not None
            and index_attempt.credential_id is not None
        ):
            connector_credential_pair_to_index_attempts[
                (index_attempt.connector_id, index_attempt.credential_id)
            ].append(index_attempt)
    indexing_statuses: list[ConnectorIndexingStatus] = []
    for (
        connector_id,
        credential_id,
    ), index_attempts in connector_credential_pair_to_index_attempts.items():        # NOTE: index_attempts is guaranteed to be length > 0
        connector = connector_id_to_connector[connector_id]
        credential_result = get_connector_credentials(
            user_id = supabase_user_id, connector_id=connector_id, credential_id=credential_id
        )
        logger.info(f"Credential: {credential_result}")
        if not credential_result:
            return  HTTPException(
                status_code=404, detail="Credential not found"
            )
        credential = credential_result[0] 
        owner = get_user_by_id(credential.user_id).email if credential.user_id else None
        index_attempts_sorted = sorted(
            index_attempts, key=lambda x: x.updated_at, reverse=True
        )
        successful_index_attempts_sorted = [
            index_attempt
            for index_attempt in index_attempts_sorted
            if index_attempt.status == IndexingStatus.SUCCESS
        ]
        logger.info(f"index_attempts_sorted: {index_attempts_sorted}")
        logger.info(f"Successful index_attempts_sorted: {successful_index_attempts_sorted}")
        indexing_statuses.append(
            ConnectorIndexingStatus(
                connector=ConnectorSnapshot.from_connector_db_model(supabase_user_id, connector),
                public_doc=credential.public_doc,
                owner=owner if owner else "",
                last_status=index_attempts_sorted[0].status,
                last_success=successful_index_attempts_sorted[0].updated_at 
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
        connector_credentials = get_connector_credentials(
            user_id = supabase_user_id, connector_id=connector.id
        )
        for credential in connector_credentials:
            if (
                connector.id,
                credential.id,
            ) not in connector_credential_pair_to_index_attempts:
                owner = get_user_by_id(credential.user_id).email if credential.user_id else None
                indexing_statuses.append(
                    ConnectorIndexingStatus(
                        connector=ConnectorSnapshot.from_connector_db_model(supabase_user_id, connector),
                        public_doc=credential.public_doc,
                        owner=owner if owner else "",
                        last_status=IndexingStatus.NOT_STARTED,
                        last_success=None,
                        docs_indexed=0,
                    ),
                )

    return indexing_statuses

@router.get("/list", response_model=list[ConnectorSnapshot], )
def get_connectors(
    supabase_user_id: str = Query(...),
) -> list[ConnectorSnapshot]:
    connectors = fetch_connectors(user_id=supabase_user_id)
    return [
        ConnectorSnapshot.from_connector_db_model(supabase_user_id, connector) for connector in connectors
    ]


@router.post("/create", response_model=ObjectCreationIdResponse)
def create_connector_from_model(
    connector_info: ConnectorBase,
    supabase_user_id: str =  Query(...)
) -> ObjectCreationIdResponse:
    try:
        result = create_connector(supabase_user_id, connector_info)
        if not result:
            raise HTTPException(status_code=409, detail="Connector already Exists")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/credential", response_model=list[CredentialSnapshot])
def get_credentials(
    supabase_user_id: str = Query(...)
) -> list[CredentialSnapshot]:
    credentials = fetch_credentials_for_user(supabase_user_id)
    return [
        CredentialSnapshot(
            id=credential.id,
            credential_json=mask_credential_dict(credential.credential_json),
            user_id=credential.user_id,
            public_doc=credential.public_doc,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
        )
        for credential in credentials
    ]

@router.post("/credential", response_model=ObjectCreationIdResponse)
def create_credential_from_model(
    connector_info: CredentialBase,
    supabase_user_id: str = Query(...),
) -> ObjectCreationIdResponse:
    return create_credential(connector_info.dict(), supabase_user_id)

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
        create_index_attempt(run_info.connector_id, credential_id, supabase_user_id)
        for credential_id in credential_ids
    ]
    return StatusResponse(
        success=True,
        message=f"Successfully created {len(index_attempt_ids)} index attempts",
        data=index_attempt_ids,
    )

@router.get(
    "/{connector_id}",
    response_model=ConnectorSnapshot,
)
def get_connector_by_id(
    connector_id: int,
    supabase_user_id: str = Query(...),
) -> ConnectorSnapshot:
    connector = fetch_connector_by_id(connector_id, supabase_user_id)
    if connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    return ConnectorSnapshot.from_connector_db_model(supabase_user_id, connector)

@router.patch(
    "/{connector_id}",
    response_model=ConnectorSnapshot | StatusResponse[int],
)
def update_connector_from_model(
    connector_id: int,
    connector_data: ConnectorBase,
    supabase_user_id: str = Query(...),
) -> ConnectorSnapshot | StatusResponse[int]:
    updated_connector = update_connector(supabase_user_id, connector_id, connector_data)
    if updated_connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    return ConnectorSnapshot.from_connector_db_model(supabase_user_id, updated_connector)


@router.delete("/{connector_id}", response_model=StatusResponse[int])
def delete_connector_by_id(
    connector_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse[int]:
    if not delete_connector(supabase_user_id, connector_id):
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )
    return StatusResponse(
        success=True, message="Credential deleted successfully", data=connector_id
    )


@router.get(
    "/credential/{credential_id}",
    response_model=CredentialSnapshot | StatusResponse[int],
)
def get_credential_by_id(
    credential_id: int,
    supabase_user_id: str = Query(...),
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
        updated_at=credential.updated_at,
    )


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
    if not delete_credential(credential_id, supabase_user_id):
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )
    return StatusResponse(
        success=True, message="Credential deleted successfully", data=credential_id
    )


@router.put("/{connector_id}/credential/{credential_id}")
def associate_credential_to_connector(
    connector_id: int,
    credential_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse[int]:
    if not add_credential_to_connector(supabase_user_id, connector_id, credential_id):
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )
    return StatusResponse(
        success=True, message="Credential associated with Connector"
    )



@router.delete("/{connector_id}/credential/{credential_id}")
def dissociate_credential_from_connector(
    connector_id: int,
    credential_id: int,
    supabase_user_id: str = Query(...),
) -> StatusResponse[int]:  
    if not remove_credential_from_connector(supabase_user_id, connector_id, credential_id):
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )
    return StatusResponse(
        success=True, message="Credential de-associated with Connector"
    )

"""
