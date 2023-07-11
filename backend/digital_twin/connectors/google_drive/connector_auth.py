"""
Ouath Flow for Google Drive
- We need to define our app's own App Credentials. This is stored in the 
    GoogleAppCredentials table.

(1) Using App credentials, we'll ask user to authenticate with Google Drive
(2) Google Drive will redirect user to our callback url with a code
(3) We'll use the code to get an access token
(4) Access Token JSON will be stored in the Credentials table.

"""
import json
from uuid import UUID
from typing import cast
from urllib.parse import ParseResult, parse_qs, urlparse
from sqlalchemy.ext.asyncio import AsyncSession

from google.auth.transport.requests import Request  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore

from digital_twin.config.app_config import WEB_DOMAIN
from digital_twin.db.model import User
from digital_twin.db.connectors.credentials import async_update_credential_json
from digital_twin.db.connectors.google_drive import (
    async_fetch_db_google_app_creds,
    async_upsert_db_google_app_cred,
)
from digital_twin.db.connectors.connectors_auth import (
    async_consume_csrf,
    async_store_csrf,
)

from digital_twin.server.model import GoogleAppCredentials
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

DB_CREDENTIALS_DICT_KEY = "google_drive_tokens"
CRED_KEY = "credential_id_{}"
GOOGLE_DRIVE_CRED_KEY = "google_drive_app_credential"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _build_frontend_google_drive_redirect() -> str:
    return f"{WEB_DOMAIN}/settings/connectors/google-drive/auth/callback"


def get_drive_tokens(
    *, creds: Credentials | None = None, token_json_str: str | None = None
) -> Credentials | None:
    if creds is None and token_json_str is None:
        return None

    if token_json_str is not None:
        creds_json = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(creds_json, SCOPES)

    if not creds:
        return None
    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            if creds.valid:
                logger.info("Refreshed Google Drive tokens.")
                return creds
        except Exception as e:
            logger.exception(f"Failed to refresh google drive access token due to: {e}")
            return None
    return None


async def async_verify_csrf(
        db_session: AsyncSession,
        credential_id: int,
        state: str
    ) -> None:
    csrf_token_obj = await async_consume_csrf(credential_id, db_session)
    if csrf_token_obj.csrf_token != state:
        raise PermissionError(
            "State from Google Drive Connector callback does not match expected"
        )


async def async_get_auth_url(
    db_session: AsyncSession,
    credential_id: int,
) -> str:
    app_cred = await async_get_google_app_cred(db_session)
    app_cred_dict = app_cred.dict()
    credential_json = {"web": app_cred_dict}
    flow = InstalledAppFlow.from_client_config(
        credential_json,
        scopes=SCOPES,
        redirect_uri=_build_frontend_google_drive_redirect(),
    )
    auth_url, _ = flow.authorization_url(prompt="consent")

    parsed_url = cast(ParseResult, urlparse(auth_url))
    params = parse_qs(parsed_url.query)

    csrf_token = params.get("state", [None])[0]
    if csrf_token:
        csrf_token = csrf_token.strip('{}')
    else:
        raise ValueError("No CSRF token provided")
    google_state = await async_store_csrf(credential_id, csrf_token, db_session)
    if not google_state:
        raise Exception("Failed to store google state in db")
    
    return str(auth_url)


async def async_update_credential_access_tokens(
    auth_code: str,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> Credentials | None:
    app_cred = await async_get_google_app_cred(db_session)
    app_cred_dict = app_cred.dict()
    credential_json = { "web": app_cred_dict }
    flow = InstalledAppFlow.from_client_config(
        credential_json,
        scopes=SCOPES,
        redirect_uri=_build_frontend_google_drive_redirect(),
    )
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    token_json_str = creds.to_json()
    new_creds_dict = {DB_CREDENTIALS_DICT_KEY: token_json_str}

    if not await async_update_credential_json(
        credential_id,
        new_creds_dict,
        organization_id,
        user,
        db_session,
    ):
        return None
    return creds


# Below are our App's Google Drive Credentials
async def async_get_google_app_cred(
    db_session: AsyncSession
) -> GoogleAppCredentials:
    app_credentials = await async_fetch_db_google_app_creds(db_session)
    if app_credentials is None:
        raise ValueError("Google Drive App Credentials not found")
    creds_str = app_credentials.credentials_json
    return GoogleAppCredentials(**json.loads(creds_str))


async def async_upsert_google_app_cred(
        app_credentials: GoogleAppCredentials, 
        db_session: AsyncSession,
) -> None:
    db_app_credentials = await async_upsert_db_google_app_cred(app_credentials.dict(), db_session)
    return GoogleAppCredentials(**json.loads(db_app_credentials.credentials_json))