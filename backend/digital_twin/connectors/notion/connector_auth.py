import requests
import secrets
import base64
import urllib.parse
from uuid import UUID
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import (
    WEB_DOMAIN,
    NOTION_CLIENT_ID, 
    NOTION_CLIENT_SECRET,
)
from digital_twin.db.connectors.connectors_auth import (
    async_consume_csrf,
    async_store_csrf,
)
from digital_twin.db.model import User
from digital_twin.db.connectors.credentials import async_update_credential_json
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

DB_CREDENTIALS_DICT_KEY = "notion_access_tokens"
BASE_URL = "https://api.notion.com"


def _build_frontend_notion_redirect() -> str:
    #return f"{WEB_DOMAIN}/connectors/notion/auth/callback"
    # TODO: Remove once done testing
    return f"{WEB_DOMAIN}/settings/admin/connectors/notion/auth/callback"


async def async_get_auth_url(
        credential_id: int,
        db_session: AsyncSession
) -> str:     
    csrf_token = secrets.token_urlsafe(32)  # Generates a URL-safe text string, containing 32 random bytes 
    db_csrf_token = await async_store_csrf(
        credential_id, 
        csrf_token, 
        db_session
    )
    if not db_csrf_token:
        raise Exception("Failed to store linear state in db")
    params = {
        "client_id": NOTION_CLIENT_ID,
        "redirect_uri": _build_frontend_notion_redirect(),
        "response_type": "code",
        "state": db_csrf_token.csrf_token,
    }

    auth_url = f"{BASE_URL}/v1/oauth/authorize?{urllib.parse.urlencode(params)}"

    
    return auth_url

async def async_verify_csrf(
    credential_id: int,
    state: str,
    db_session: AsyncSession,
) -> None:
    csrf_token_obj = await async_consume_csrf(credential_id, db_session)
    if csrf_token_obj.csrf_token != state:
        raise PermissionError(
            "State from Linear callback does not match expected"
        )


async def async_update_credential_access_tokens(
    auth_code: str,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> Dict[str, str] | None:

    # encode in base 64
    encoded = base64.b64encode(f"{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded}", 
        "Content-Type": "application/json", 
        "Notion-Version": "2022-06-28"
    }

    data = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': _build_frontend_notion_redirect()
    }

    response = requests.post(f"{BASE_URL}/v1/oauth/token", headers=headers, json=data)

    if response.status_code == 200:
        creds = response.json()
        new_creds_dict = {DB_CREDENTIALS_DICT_KEY: creds["access_token"]}

        if not await async_update_credential_json(
            credential_id, 
            new_creds_dict,
            organization_id,
            user,
            db_session,
        ):
            return None
        return creds
    else:
        logger.exception(f"Failed to update notion access token due to: {response.text}")
        return None