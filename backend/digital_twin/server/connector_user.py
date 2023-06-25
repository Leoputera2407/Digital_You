from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session

from digital_twin.config.app_config import IS_DEV
from digital_twin.auth.users import current_user
from digital_twin.db.engine import get_session

from digital_twin.server.model import (
    AuthUrl,
    ConnectorSnapshot,
    CredentialBase,
    CredentialSnapshot,
    GDriveCallback,
    NotionCallback,
    # GoogleAppWebCredentials,
    ObjectCreationIdResponse,
    StatusResponse,
)
from digital_twin.db.model import (
    Credential,
    User,
)

from digital_twin.connectors.notion.connector_auth import (
    get_auth_url as get_notion_auth_url,
    update_credential_access_tokens as update_notion_credential_access_tokens,
)

from digital_twin.connectors.google_drive.connector_auth import (
    DB_CREDENTIALS_DICT_KEY,
    get_auth_url as get_gdrive_auth_url,
    update_credential_access_tokens as update_gdrive_credential_access_tokens,
    # upsert_google_app_cred,
    verify_csrf as verify_gdrive_csrf,
)
from digital_twin.db.connectors.connector_credential_association import (
    add_credential_to_connector,
    remove_credential_from_connector,
)
from digital_twin.db.connectors.connectors import (
    fetch_connector_by_id,
    fetch_connectors,
)
from digital_twin.db.connectors.credentials import (
    fetch_credentials,
    create_credential,
    delete_credential,
    update_credential,
    fetch_credential_by_id,
    mask_credential_dict,
)

router = APIRouter(prefix="/connector")


_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME = "google_drive_credential_id"

@router.get("/google-drive/authorize/{credential_id}", response_model=AuthUrl)
def google_drive_auth(
    response: Response, 
    credential_id: str,
    _: User = Depends(current_user),
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
    callback: GDriveCallback = Depends(),
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    credential_id = int(credential_id_cookie)
    verify_gdrive_csrf(credential_id, callback.state)
    if (
        update_gdrive_credential_access_tokens(callback.code, credential_id, user, db_session)
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Google Drive access tokens"
        )

    return StatusResponse(success=True, message="Updated Google Drive access tokens")


_NOTION_CREDENTIAL_ID_COOKIE_NAME = "notion_credential_id"

@router.get("/notion/authorize/{credential_id}", response_model=AuthUrl)
def notion_auth(
    response: Response, 
    credential_id: str,
    _: User = Depends(current_user),
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
    callback: NotionCallback = Depends(),
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_NOTION_CREDENTIAL_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    credential_id = int(credential_id_cookie)
    if (
        update_notion_credential_access_tokens(
            callback.code, 
            credential_id, 
            user,
            db_session,
        )
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Notion access tokens"
        )

    return StatusResponse(success=True, message="Updated Notion access tokens")

# TODO: Workaround, should remove on deployment once we figure out Cross-site Cookie
if IS_DEV:
    @router.get("/google-drive-non-prod/callback")
    def google_drive_callback_non_prod(
        callback: GDriveCallback = Depends(),
        user: User = Depends(current_user),
        db_session: Session = Depends(get_session),
    ) -> StatusResponse:
        credentials: List[Credential] = fetch_credentials(user, db_session)
        credential_with_empty_json = next((credential for credential in credentials if not credential.credential_json), None)
        if credential_with_empty_json is None:
            raise HTTPException(
                status_code=500, detail="Unable to fetch Google Drive access tokens"
            )
        if (
            update_gdrive_credential_access_tokens(
                callback.code, 
                credential_with_empty_json.id, 
                user,
                db_session
            )
            is None
        ):
            raise HTTPException(
                status_code=500, detail="Unable to fetch Google Drive access tokens"
            )

        return StatusResponse(success=True, message="Updated Google Drive access tokens")

    @router.get("/notion-non-prod/callback")
    def notion_callback_non_prod(
        callback: NotionCallback = Depends(),
        user: User = Depends(current_user),
        db_session: Session = Depends(get_session),
    ) -> StatusResponse:
       from digital_twin.connectors.notion.connector_auth import  DB_CREDENTIALS_DICT_KEY
       credentials: List[Credential] = fetch_credentials(user, db_session)
       credential_with_empty_json = next((credential for credential in credentials if not credential.credential_json), None)
       # Find first creds with empty_json just 
       if credential_with_empty_json is None:
            raise HTTPException(
                status_code=500, detail="Unable to fetch Notion access tokens"
            )
       if (
            update_notion_credential_access_tokens(
                callback.code, 
                credential_with_empty_json.id, 
                user,
                db_session
            )
            is None
        ):
            raise HTTPException(
                status_code=500, detail="Unable to fetch Notion access tokens"
            )
       
       return StatusResponse(success=True, message="Updated Notion access tokens")


@router.get("/list", response_model=list[ConnectorSnapshot], )
def get_connectors(
     _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[ConnectorSnapshot]:
    connectors = fetch_connectors(db_session)
    return [
        ConnectorSnapshot.from_connector_db_model(connector) for connector in connectors
    ]

@router.get("/{connector_id}")
def get_connector_by_id(
    connector_id: int,
    _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> ConnectorSnapshot | StatusResponse[int]:
    connector = fetch_connector_by_id(connector_id, db_session)
    if connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    return ConnectorSnapshot(
        id=connector.id,
        name=connector.name,
        source=connector.source,
        input_type=connector.input_type,
        connector_specific_config=connector.connector_specific_config,
        refresh_freq=connector.refresh_freq,
        credential_ids=[
            association.credential.id for association in connector.credentials
        ],
        time_created=connector.created_at,
        time_updated=connector.updated_at,
        disabled=connector.disabled,
    )

@router.get("/credential")
def get_credentials(
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[CredentialSnapshot]:
    credentials = fetch_credentials(user, db_session)
    return [
        CredentialSnapshot(
            id=credential.id,
            credential_json=mask_credential_dict(credential.credential_json),
            user_id=credential.user_id,
            public_doc=credential.public_doc,
            time_created=credential.created_at,
            time_updated=credential.updated_at,
        )
        for credential in credentials
    ]

@router.get("/credential/{credential_id}")
def get_credential_by_id(
    credential_id: int,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> CredentialSnapshot | StatusResponse[int]:
    credential = fetch_credential_by_id(credential_id, user, db_session)
    if credential is None:
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )

    return CredentialSnapshot(
        id=credential.id,
        credential_json=mask_credential_dict(credential.credential_json),
        user_id=credential.user_id,
        public_doc=credential.public_doc,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )


@router.post("/credential")
def create_credential_from_model(
    connector_info: CredentialBase,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> ObjectCreationIdResponse:
    return create_credential(connector_info, user, db_session)

@router.patch("/credential/{credential_id}")
def update_credential_from_model(
    credential_id: int,
    credential_data: CredentialBase,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> CredentialSnapshot | StatusResponse[int]:
    updated_credential = update_credential(
        credential_id, credential_data, user, db_session
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
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    delete_credential(credential_id, user, db_session)
    return StatusResponse(
        success=True, message="Credential deleted successfully", data=credential_id
    )


@router.put("/{connector_id}/credential/{credential_id}")
def associate_credential_to_connector(
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse[int]:
    return add_credential_to_connector(connector_id, credential_id, user, db_session)



@router.delete("/{connector_id}/credential/{credential_id}")
def dissociate_credential_from_connector(
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse[int]:
    return remove_credential_from_connector(
        connector_id, credential_id, user, db_session
    )

