from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.users import current_user
from digital_twin.config.app_config import IS_DEV
from digital_twin.connectors.google_drive.connector_auth import DB_CREDENTIALS_DICT_KEY
from digital_twin.connectors.google_drive.connector_auth import (
    async_get_auth_url as async_get_gdrive_auth_url,
)
from digital_twin.connectors.google_drive.connector_auth import (
    async_update_credential_access_tokens as async_update_gdrive_credential_access_tokens,
)
from digital_twin.connectors.google_drive.connector_auth import async_verify_csrf as async_verify_gdrive_csrf
from digital_twin.connectors.linear.connector_auth import async_get_auth_url as async_get_linear_auth_url
from digital_twin.connectors.linear.connector_auth import (
    async_update_credential_access_tokens as async_update_linear_credential_access_tokens,
)
from digital_twin.connectors.linear.connector_auth import async_verify_csrf as async_verify_linear_csrf
from digital_twin.connectors.notion.connector_auth import async_get_auth_url as async_get_notion_auth_url
from digital_twin.connectors.notion.connector_auth import (
    async_update_credential_access_tokens as async_update_notion_credential_access_tokens,
)
from digital_twin.connectors.notion.connector_auth import async_verify_csrf as async_verify_notion_csrf
from digital_twin.db.connectors.connector_credential_pair import (
    async_add_credential_to_connector,
    async_remove_credential_from_connector,
)
from digital_twin.db.connectors.connectors import (
    async_create_connector,
    async_fetch_connector_by_id_and_org,
    async_fetch_connectors,
)
from digital_twin.db.connectors.credentials import (
    async_create_credential,
    async_delete_credential,
    async_fetch_credential_by_id_and_org,
    async_fetch_credentials,
    async_update_credential,
    mask_credential_dict,
)
from digital_twin.db.engine import get_async_session_generator
from digital_twin.db.model import User
from digital_twin.server.model import (
    AuthUrl,
    ConnectorBase,
    ConnectorSnapshot,
    CredentialBase,
    CredentialSnapshot,
    GDriveCallback,
    LinearCallback,
    NotionCallback,
    ObjectCreationIdResponse,
    StatusResponse,
)
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

router = APIRouter(prefix="/connector")


_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME = "google_drive_credential_id"
_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME = "google_drive_organization_id"


@router.get("/{organization_id}/google-drive/authorize/{credential_id}", response_model=AuthUrl)
async def google_drive_auth(
    response: Response,
    organization_id: UUID,
    credential_id: int,
    _: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )

    # set a cookie for the organization_id
    response.set_cookie(
        key=_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME,
        value=str(organization_id),
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )
    auth_url = await async_get_gdrive_auth_url(db_session, int(credential_id))
    return AuthUrl(auth_url=auth_url)


@router.get("/google-drive/callback")
async def google_drive_callback(
    request: Request,
    callback: GDriveCallback = Depends(),
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_GOOGLE_DRIVE_CREDENTIAL_ID_COOKIE_NAME)
    organization_id_cookie = request.cookies.get(_GOOGLE_DRIVE_ORGANIZATION_ID_COOKIE_NAME)
    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(status_code=401, detail="Credential ID did not pass verification.")
    if organization_id_cookie is None:
        raise HTTPException(status_code=401, detail="Organization ID did not pass verification.")
    credential_id = int(credential_id_cookie)
    organization_id = UUID(organization_id_cookie)
    await async_verify_gdrive_csrf(db_session, credential_id, callback.state)
    if (
        await async_update_gdrive_credential_access_tokens(
            callback.code, credential_id, organization_id, user, db_session
        )
        is None
    ):
        raise HTTPException(status_code=500, detail="Unable to fetch Google Drive access tokens")

    return StatusResponse(success=True, message="Updated Google Drive access tokens")


_NOTION_CREDENTIAL_ID_COOKIE_NAME = "notion_credential_id"
_NOTION_ORGANIZATION_ID_COOKIE_NAME = "notion_organization_id"


@router.get("/{organization_id}/notion/authorize/{credential_id}", response_model=AuthUrl)
async def notion_auth(
    response: Response,
    organization_id: UUID,
    credential_id: int,
    _: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=_NOTION_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )
    response.set_cookie(
        key=_NOTION_ORGANIZATION_ID_COOKIE_NAME,
        value=str(organization_id),
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )
    auth_url = await async_get_notion_auth_url(
        credential_id,
        db_session,
    )
    return AuthUrl(auth_url=auth_url)


@router.get("/notion/callback")
async def notion_callback(
    request: Request,
    callback: NotionCallback = Depends(),
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(_NOTION_CREDENTIAL_ID_COOKIE_NAME)
    organization_id_cookie = request.cookies.get(_NOTION_ORGANIZATION_ID_COOKIE_NAME)

    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(status_code=401, detail="Credential ID did not pass verification.")
    if organization_id_cookie is None:
        raise HTTPException(status_code=401, detail="Organization ID did not pass verification.")
    credential_id = int(credential_id_cookie)
    organization_id = UUID(organization_id_cookie)
    await async_verify_notion_csrf(credential_id, callback.state, db_session)
    if (
        await async_update_notion_credential_access_tokens(
            callback.code,
            credential_id,
            organization_id,
            user,
            db_session,
        )
        is None
    ):
        raise HTTPException(status_code=500, detail="Unable to fetch Notion access tokens")

    return StatusResponse(success=True, message="Updated Notion access tokens")


LINEAR_CREDENTIAL_ID_COOKIE_NAME = "linear_credential_id"
LINEAR_ORGANIZATION_ID_COOKIE_NAME = "linear_organization_id"


@router.get("/{organization_id}/linear/authorize/{credential_id}", response_model=AuthUrl)
async def linear_auth(
    response: Response,
    organization_id: UUID,
    credential_id: int,
    _: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthUrl:
    # set a cookie that we can read in the callback (used for `verify_csrf`)
    response.set_cookie(
        key=LINEAR_CREDENTIAL_ID_COOKIE_NAME,
        value=credential_id,
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )
    response.set_cookie(
        key=LINEAR_ORGANIZATION_ID_COOKIE_NAME,
        value=str(organization_id),
        # TODO: this is sketch, but the only way
        # I can think of doing cross-site cookies,
        # without sub-domains/reverse proxy
        # httponly=True,
        samesite="None",
        secure=True,
        max_age=600,
    )
    auth_url = await async_get_linear_auth_url(
        credential_id,
        db_session,
    )
    return AuthUrl(auth_url=auth_url)


@router.get("/linear/callback")
async def linear_callback(
    request: Request,
    callback: LinearCallback = Depends(),
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    credential_id_cookie = request.cookies.get(LINEAR_CREDENTIAL_ID_COOKIE_NAME)
    organization_id_cookie = request.cookies.get(LINEAR_ORGANIZATION_ID_COOKIE_NAME)

    if credential_id_cookie is None or not credential_id_cookie.isdigit():
        raise HTTPException(status_code=401, detail="Request did not pass CSRF verification.")
    if organization_id_cookie is None:
        raise HTTPException(status_code=401, detail="Organization ID did not pass verification.")
    credential_id = int(credential_id_cookie)
    organization_id = UUID(organization_id_cookie)
    await async_verify_linear_csrf(credential_id, callback.state, db_session)
    if (
        await async_update_linear_credential_access_tokens(
            callback.code,
            credential_id,
            organization_id,
            user,
            db_session,
        )
        is None
    ):
        raise HTTPException(status_code=500, detail="Unable to fetch Linear access tokens")

    return StatusResponse(success=True, message="Updated Linear access tokens")


@router.post("/{organization_id}/create", response_model=ObjectCreationIdResponse)
async def create_personal_connector_from_model(
    connector_info: ConnectorBase,
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> ObjectCreationIdResponse:
    try:
        return await async_create_connector(
            connector_info,
            organization_id,
            db_session,
            user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{organization_id}/list", response_model=list[ConnectorSnapshot])
async def get_connectors(
    organization_id: UUID,
    _: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> list[ConnectorSnapshot]:
    connectors = await async_fetch_connectors(
        db_session,
        organization_id=organization_id,
    )
    return [ConnectorSnapshot.from_connector_db_model(connector) for connector in connectors]


@router.get("/{organization_id}/credential")
async def get_personal_credentials(
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> list[CredentialSnapshot]:
    credentials = await async_fetch_credentials(
        organization_id,
        db_session,
        user=user,
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
async def get_credential_by_id(
    credential_id: int,
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> CredentialSnapshot | StatusResponse[int]:
    credential = await async_fetch_credential_by_id_and_org(credential_id, user, organization_id, db_session)
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
async def create_credential_from_model(
    organization_id: UUID,
    connector_info: CredentialBase,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> ObjectCreationIdResponse:
    return await async_create_credential(connector_info, user, organization_id, db_session)


@router.patch("/{organization_id}/credential/{credential_id}")
async def update_credential_from_model(
    credential_id: int,
    organization_id: UUID,
    credential_data: CredentialBase,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> CredentialSnapshot | StatusResponse[int]:
    updated_credential = await async_update_credential(
        credential_id, credential_data, user, organization_id, db_session
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
async def delete_credential_by_id(
    credential_id: int,
    organization_id: UUID,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse:
    await async_delete_credential(credential_id, user, organization_id, db_session)
    return StatusResponse(success=True, message="Credential deleted successfully", data=credential_id)


@router.get("/{organization_id}/{connector_id}")
async def get_connector_by_id(
    connector_id: int,
    organization_id: UUID,
    _: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> ConnectorSnapshot | StatusResponse[int]:
    connector = await async_fetch_connector_by_id_and_org(connector_id, organization_id, db_session)
    if connector is None:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} does not exist")

    return ConnectorSnapshot(
        id=connector.id,
        name=connector.name,
        source=connector.source,
        input_type=connector.input_type,
        connector_specific_config=connector.connector_specific_config,
        refresh_freq=connector.refresh_freq,
        credential_ids=[association.credential.id for association in connector.credentials],
        created_at=connector.created_at,
        updated_at=connector.updated_at,
        disabled=connector.disabled,
    )


@router.put("/{organization_id}/{connector_id}/credential/{credential_id}")
async def associate_credential_to_connector(
    organization_id: UUID,
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[int]:
    return await async_add_credential_to_connector(
        connector_id,
        credential_id,
        organization_id,
        user,
        db_session,
    )


@router.delete("/{organization_id}/{connector_id}/credential/{credential_id}")
async def dissociate_credential_from_connector(
    organization_id: UUID,
    connector_id: int,
    credential_id: int,
    user: User = Depends(current_user),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[int]:
    return await async_remove_credential_from_connector(
        connector_id, credential_id, organization_id, user, db_session
    )
