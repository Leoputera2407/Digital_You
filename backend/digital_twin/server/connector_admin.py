from typing import Optional
from uuid import UUID

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.auth.users import current_admin_for_org
from digital_twin.connectors.google_drive.connector_auth import (
    DB_CREDENTIALS_DICT_KEY,
    async_get_google_app_cred,
    get_drive_tokens,
)
from digital_twin.connectors.linear.graphql import LinearGraphQLClient
from digital_twin.db.connectors.connector_credential_pair import async_get_connector_credential_pairs
from digital_twin.db.connectors.connectors import (
    async_create_connector,
    async_delete_connector,
    async_get_connector_credential_ids,
    async_update_connector,
)
from digital_twin.db.connectors.credentials import (
    async_fetch_credential_by_id_and_org,
    async_fetch_credentials,
    mask_credential_dict,
)
from digital_twin.db.connectors.index_attempt import create_index_attempt
from digital_twin.db.engine import get_async_session_generator
from digital_twin.db.model import Credential, User
from digital_twin.server.model import (
    AuthStatus,
    ConfluenceTestRequest,
    ConnectorBase,
    ConnectorIndexingStatus,
    ConnectorSnapshot,
    CredentialSnapshot,
    GithubTestRequest,
    LinearOrganizationSnapshot,
    NotionWorkspaceSnapshot,
    ObjectCreationIdResponse,
    RunConnectorRequest,
    StatusResponse,
)
from digital_twin.utils.logging import setup_logger

router = APIRouter(prefix="/connector/admin")

logger = setup_logger()


@router.get("/{organization_id}/google-drive/app-credential")
async def async_check_google_app_credentials_exist(
    organization_id: UUID,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> dict[str, str]:
    try:
        google_app_cred = await async_get_google_app_cred(db_session)
        return {"client_id": google_app_cred.client_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Google App Credentials not found")


# TODO: Don't expose this methods below as we don't want people over-writing our app creds
# Maybe admin level makes sense later
"""
@router.put("/google-drive/app-credential")
def update_google_app_credentials(
    _: User = Depends(current_admin_for_org),
    app_credentials: GoogleAppWebCredentials,
) -> StatusResponse:
    try:
        await async_upsert_google_app_cred(app_credentials.web)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StatusResponse(
        success=True, message="Successfully saved Google App Credentials"
    )
"""


@router.get("/{organization_id}/google-drive/check-auth/{credential_id}")
async def check_drive_tokens(
    organization_id: UUID,
    credential_id: int,
    admin_user: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> AuthStatus:
    db_credentials: Optional[Credential] = await async_fetch_credential_by_id_and_org(
        credential_id,
        admin_user,
        organization_id,
        db_session,
    )
    if not db_credentials or DB_CREDENTIALS_DICT_KEY not in db_credentials.credential_json:
        return AuthStatus(authenticated=False)
    token_json_str = str(db_credentials.credential_json[DB_CREDENTIALS_DICT_KEY])
    google_drive_creds = get_drive_tokens(token_json_str=token_json_str)
    if google_drive_creds is None:
        return AuthStatus(authenticated=False)
    return AuthStatus(authenticated=True)


@router.get("/{organization_id}/indexing-status")
async def get_connector_indexing_status(
    organization_id: UUID,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> list[ConnectorIndexingStatus]:
    indexing_statuses: list[ConnectorIndexingStatus] = []

    cc_pairs = await async_get_connector_credential_pairs(db_session, organization_id)
    for cc_pair in cc_pairs:
        connector = cc_pair.connector
        credential = cc_pair.credential
        indexing_statuses.append(
            ConnectorIndexingStatus(
                connector=ConnectorSnapshot.from_connector_db_model(connector),
                public_doc=credential.public_doc,
                owner=credential.user.email if credential.user else "",
                last_status=cc_pair.last_attempt_status,
                last_success=cc_pair.last_successful_index_time,
                docs_indexed=cc_pair.total_docs_indexed,
            )
        )

    return indexing_statuses


@router.get("/{organization_id}/admin-credential")
async def get_admin_credentials(
    organization_id: UUID,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> list[CredentialSnapshot]:
    credentials = await async_fetch_credentials(
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


@router.post("/{organization_id}/create", response_model=ObjectCreationIdResponse)
async def admin_create_connector_from_model(
    connector_info: ConnectorBase,
    organization_id: UUID,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> ObjectCreationIdResponse:
    try:
        return await async_create_connector(
            connector_info,
            organization_id,
            db_session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{organization_id}/{connector_id}")
async def update_connector_from_model(
    connector_id: int,
    organization_id: UUID,
    connector_data: ConnectorBase,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> ConnectorSnapshot | StatusResponse[int]:
    updated_connector = await async_update_connector(
        connector_id, connector_data, organization_id, db_session
    )
    if updated_connector is None:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} does not exist")

    return ConnectorSnapshot(
        id=updated_connector.id,
        name=updated_connector.name,
        source=updated_connector.source,
        input_type=updated_connector.input_type,
        connector_specific_config=updated_connector.connector_specific_config,
        refresh_freq=updated_connector.refresh_freq,
        credential_ids=[association.credential.id for association in updated_connector.credentials],
        created_at=updated_connector.created_at,
        updated_at=updated_connector.updated_at,
        disabled=updated_connector.disabled,
    )


@router.delete("/{organization_id}/{connector_id}", response_model=StatusResponse[int])
async def delete_connector_by_id(
    connector_id: int,
    organization_id: UUID,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[int]:
    return await async_delete_connector(
        connector_id,
        organization_id,
        db_session,
    )


@router.post("/{organization_id}/run-once")
async def connector_run_once(
    organization_id: UUID,
    run_info: RunConnectorRequest,
    _: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> StatusResponse[list[int]]:
    connector_id = run_info.connector_id
    specified_credential_ids = run_info.credential_ids
    try:
        possible_credential_ids = await async_get_connector_credential_ids(
            run_info.connector_id,
            organization_id,
            db_session,
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Connector by id {connector_id} does not exist.",
        )

    if not specified_credential_ids:
        credential_ids = possible_credential_ids
    else:
        if set(specified_credential_ids).issubset(set(possible_credential_ids)):
            credential_ids = specified_credential_ids
        else:
            raise HTTPException(
                status_code=400,
                detail="Not all specified credentials are associated with connector",
            )

    if not credential_ids:
        raise HTTPException(
            status_code=400,
            detail="Connector has no valid credentials, cannot create index attempts.",
        )

    index_attempt_ids = [
        create_index_attempt(run_info.connector_id, credential_id, db_session)
        for credential_id in credential_ids
    ]
    return StatusResponse(
        success=True,
        message=f"Successfully created {len(index_attempt_ids)} index attempts",
        data=index_attempt_ids,
    )


@router.post("/{organization_id}/test-github", response_model=StatusResponse[bool])
async def test_github_access_token(
    organization_id: UUID,  # type: ignore
    github_test_info: GithubTestRequest,
    _: User = Depends(current_admin_for_org),
) -> StatusResponse[bool]:
    from github import BadCredentialsException, Github, GithubException, UnknownObjectException

    try:
        github_client = Github(github_test_info.access_token_value)
        _ = github_client.get_user()
        return StatusResponse(success=True, data=True)
    except UnknownObjectException:
        return StatusResponse(
            success=False,
            message="Invalid repository name or repository owner.",
            data=False,
        )
    except BadCredentialsException:
        return StatusResponse(success=False, message="Invalid Github access token.", data=False)
    except GithubException as e:
        return StatusResponse(success=False, message=f"An error occurred: {e}", data=False)
    except Exception as e:
        return StatusResponse(
            success=False,
            message=f"Failed to validate Github access token: {str(e)}",
            data=False,
        )


@router.post("/{organization_id}/test-confluence", response_model=StatusResponse[bool])
async def test_confluence_access_token(
    organization_id: UUID,  # type: ignore
    confluence_test_info: ConfluenceTestRequest,
    _: User = Depends(current_admin_for_org),
) -> StatusResponse[bool]:
    from atlassian import Confluence
    from atlassian.errors import ApiNotFoundError, ApiPermissionError

    try:
        confluence_client = Confluence(
            url=confluence_test_info.wiki_page_url,
            username=confluence_test_info.confluence_username,
            password=confluence_test_info.confluence_access_token,
            cloud=True,
        )
        # If the token is invalid or we don't have access, this will raise an exception
        _ = confluence_client.get_user_details_by_username(username=confluence_test_info.confluence_username)
        return StatusResponse[bool](
            success=True,
            message="Successfully validated Confluence access token.",
            data=True,
        )
    except ApiNotFoundError:
        return StatusResponse(success=False, message="Wiki page not found.", data=False)
    except ApiPermissionError:
        return StatusResponse(
            success=False,
            message="Invalid Confluence username or access token.",
            data=False,
        )
    except Exception as e:
        return StatusResponse(
            success=False,
            message=f"Failed to validate Confluence access token: {str(e)}",
            data=False,
        )


@router.get("/{organization_id}/get-linear-org-and-team")
async def get_linear_org_and_teams(
    organization_id: UUID,
    linear_credential_id: int,
    admin_user: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> LinearOrganizationSnapshot:
    linear_credential = await async_fetch_credential_by_id_and_org(
        linear_credential_id, admin_user, organization_id, db_session
    )

    if linear_credential is None:
        raise HTTPException(
            status_code=404,
            detail="Linear credential not found",
        )
    access_token = linear_credential.credential_json.get("linear_access_tokens")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid Linear credential, access_token not found",
        )

    try:
        linear_service = LinearGraphQLClient(access_token)
        linear_org_and_teams = linear_service.get_user_organization_and_teams()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Linear organization and teams: {str(e)}",
        )

    return LinearOrganizationSnapshot(
        name=linear_org_and_teams.name,
        teams=linear_org_and_teams.teams,
    )


@router.get("/{organization_id}/get-notion-workspace")
async def get_notion_workspace(
    organization_id: UUID,
    notion_credential_id: int,
    admin_user: User = Depends(current_admin_for_org),
    db_session: AsyncSession = Depends(get_async_session_generator),
) -> NotionWorkspaceSnapshot:
    notion_credential = await async_fetch_credential_by_id_and_org(
        notion_credential_id, admin_user, organization_id, db_session
    )

    if notion_credential is None:
        raise HTTPException(
            status_code=404,
            detail="Notion credential not found",
        )
    access_token = notion_credential.credential_json.get("notion_access_tokens")
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid Notion credential, access_token not found",
        )

    try:
        # Define your headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        # Define your endpoint
        url = "https://api.notion.com/v1/users/me"

        # Make the request
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch Notion workspace: {response.text}",
            )

        workspace_data = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Notion workspace: {str(e)}",
        )

    return NotionWorkspaceSnapshot(
        name=workspace_data["bot"]["workspace_name"],
    )
