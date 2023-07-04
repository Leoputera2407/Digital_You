from typing import List
from uuid import UUID
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
from digital_twin.db.connectors.connector_credential_pair import (
    add_credential_to_connector,
    remove_credential_from_connector,
)
from digital_twin.db.connectors.connectors import (
    fetch_connector_by_id_and_org,
    fetch_connectors,
)
from digital_twin.db.connectors.credentials import (
    fetch_credentials,
    create_credential,
    delete_credential,
    update_credential,
    fetch_credential_by_id_and_org,
    mask_credential_dict,
)

router = APIRouter(prefix="/connector")


_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME = "google_drive_credential_id"
_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME = "google_drive_organization_id"

@router.get("/{organization_id}/google-drive/authorize/{credential_id}", response_model=AuthUrl)
def google_drive_auth(
    response: Response, 
    organization_id: UUID,
    credential_id: str,
    _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        httponly=True,
        samesite='None',
        secure=True,
        max_age=600,
    )

    # set a cookie for the organization_id
    response.set_cookie(
        key=_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME,
        value=str(organization_id),
        httponly=True,
        samesite='None',
        secure=True,
        max_age=600,
    )
    
    return AuthUrl(auth_url=get_gdrive_auth_url(db_session, int(credential_id)))

@router.get("/google-drive/callback")
def google_drive_callback(
    request: Request,
    callback: GDriveCallback = Depends(),
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME)
    organization_id_cookie = request.cookies.get(_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME)
    from digital_twin.utils.logging import setup_logger
    logger = setup_logger()
    logger.info(f"credential_id_cookie: {credential_id_cookie}")
    logger.info(f"organization_id_cookie: {organization_id_cookie}")
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    if organization_id_cookie is None:
        raise HTTPException(
            status_code=401, detail="Organization ID did not pass verification."
        )
    credential_id = int(credential_id_cookie)
    organization_id = UUID(organization_id_cookie)
    verify_gdrive_csrf(credential_id, callback.state)
    if (
        update_gdrive_credential_access_tokens(
            callback.code, 
            credential_id,
            organization_id,
            user,
            db_session
        )
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Google Drive access tokens"
        )

    return StatusResponse(success=True, message="Updated Google Drive access tokens")


_NOTION_CREDENTIAL_ID_COOKIE_NAME = "notion_credential_id"
_NOTION_ORGANIZATION_ID_COOKIE_NAME = "notion_organization_id"

@router.get("/{organization_id}/notion/authorize/{credential_id}", response_model=AuthUrl)
def notion_auth(
    response: Response, 
    organization_id: UUID,
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
    response.set_cookie(
        key=_NOTION_ORGANIZATION_ID_COOKIE_NAME,
        value=str(organization_id),
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
    organization_id_cookie = request.cookies.get(_NOTION_ORGANIZATION_ID_COOKIE_NAME)

    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(
            status_code=401, detail="Request did not pass CSRF verification."
        )
    if organization_id_cookie is None:
        raise HTTPException(
            status_code=401, detail="Organization ID did not pass verification."
        )
    credential_id = int(credential_id_cookie)
    organization_id = UUID(organization_id_cookie)
    if (
        update_notion_credential_access_tokens(
            callback.code, 
            credential_id, 
            organization_id,
            user,
            db_session,
        )
        is None
    ):
        raise HTTPException(
            status_code=500, detail="Unable to fetch Notion access tokens"
        )

    return StatusResponse(success=True, message="Updated Notion access tokens")

@router.get("/{organization_id}/list", response_model=list[ConnectorSnapshot], )
def get_connectors(
    organization_id: UUID,
     _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[ConnectorSnapshot]:
    connectors = fetch_connectors(
        db_session,
        organization_id=organization_id,
    )
    return [
        ConnectorSnapshot.from_connector_db_model(connector) for connector in connectors
    ]

@router.get("/{organization_id}/credential")
def get_credentials(
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[CredentialSnapshot]:
    credentials = fetch_credentials(
        user, 
        organization_id,
        db_session,
    )
    return [
        CredentialSnapshot(
            id=credential.id,
            credential_json=mask_credential_dict(credential.credential_json),
            user_id=str(credential.user_id),
            public_doc=credential.public_doc,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
        )
        for credential in credentials
    ]

@router.get("/{organization_id}/credential/{credential_id}")
def get_credential_by_id(
    credential_id: int,
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> CredentialSnapshot | StatusResponse[int]:
    credential = fetch_credential_by_id_and_org(
        credential_id, 
        user, 
        organization_id,
        db_session
    )
    if credential is None:
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )

    return CredentialSnapshot(
        id=credential.id,
        credential_json=mask_credential_dict(credential.credential_json),
        user_id=str(credential.user_id),
        public_doc=credential.public_doc,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )


@router.post("/{organization_id}/credential")
def create_credential_from_model(
    organization_id: UUID,
    connector_info: CredentialBase,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> ObjectCreationIdResponse:
    return create_credential(
        connector_info, 
        user,
        organization_id,
        db_session
    )

@router.patch("/{organization_id}/credential/{credential_id}")
def update_credential_from_model(
    credential_id: int,
    organization_id: UUID,
    credential_data: CredentialBase,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> CredentialSnapshot | StatusResponse[int]:
    updated_credential = update_credential(
        credential_id,
        credential_data,
        user,
        organization_id,
        db_session
    )
    if updated_credential is None:
        raise HTTPException(
            status_code=401,
            detail=f"Credential {credential_id} does not exist or does not belong to user",
        )

    return CredentialSnapshot(
        id=updated_credential.id,
        credential_json=updated_credential.credential_json,
        user_id=str(updated_credential.user_id),
        public_doc=updated_credential.public_doc,
        created_at=updated_credential.created_at,
        updated_at=updated_credential.updated_at,
    )


@router.delete("/{organization_id}/credential/{credential_id}", response_model=StatusResponse[int])
def delete_credential_by_id(
    credential_id: int,
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse:
    delete_credential(
        credential_id,
        user,
        organization_id,
        db_session
    )
    return StatusResponse(
        success=True, message="Credential deleted successfully", data=credential_id
    )


@router.get("/{organization_id}/{connector_id}")
def get_connector_by_id(
    connector_id: int,
    organization_id: UUID,
    _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> ConnectorSnapshot | StatusResponse[int]:
    connector = fetch_connector_by_id_and_org(
        connector_id, 
        organization_id,
        db_session
    )
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
        created_at=connector.created_at,
        updated_at=connector.updated_at,
        disabled=connector.disabled,
    )

@router.put("/{organization_id}/{connector_id}/credential/{credential_id}")
def associate_credential_to_connector(
    organization_id: UUID,
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse[int]:
    return add_credential_to_connector(
        connector_id, 
        credential_id, 
        organization_id,
        user, 
        db_session,
    )



@router.delete("/{organization_id}/{connector_id}/credential/{credential_id}")
def dissociate_credential_from_connector(
    organization_id: UUID,
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StatusResponse[int]:
    return remove_credential_from_connector(
        connector_id, 
        credential_id, 
        organization_id,
        user, 
        db_session
    )

