import json
import requests
import secrets
import urllib.parse
from uuid import UUID
from typing import Dict
from sqlalchemy.orm import Session

from digital_twin.config.app_config import (
    WEB_DOMAIN,
    LINEAR_CLIENT_ID, 
    LINEAR_CLIENT_SECRET,
)
from digital_twin.db.connectors.connectors_auth import (
    consume_csrf,
    store_csrf,
)
from digital_twin.db.model import User
from digital_twin.db.connectors.credentials import update_credential_json
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

DB_CREDENTIALS_DICT_KEY = "linear_access_tokens"
BASE_URL = "https://linear.app"
API_BASE_URL = "https://api.linear.app"

def _build_frontend_linear_redirect() -> str:
    return f"{WEB_DOMAIN}/settings/connectors/linear/auth/callback"


def get_auth_url(credential_id: int, db_session: Session) -> str:
    csrf_token = secrets.token_urlsafe(32)  # Generates a URL-safe text string, containing 32 random bytes 
    db_csrf_token = store_csrf(credential_id, csrf_token, db_session)
    if not db_csrf_token:
        raise Exception("Failed to store linear state in db")

    params = {
        "client_id": LINEAR_CLIENT_ID,
        "redirect_uri": _build_frontend_linear_redirect(),
        "response_type": "code",
        "scope": "read", 
        "prompt": "consent",
        "state": db_csrf_token.csrf_token, 
    }

    auth_url = f"{BASE_URL}/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    return auth_url

def verify_csrf(
    credential_id: int,
    state: str,
    db_session: Session,
) -> None:
    csrf_token_obj = consume_csrf(credential_id, db_session)
    if csrf_token_obj.csrf_token != state:
        raise PermissionError(
            "State from Linear callback does not match expected"
        )

def update_credential_access_tokens(
    auth_code: str,
    credential_id: int,
    organization_id: UUID,
    user: User,
    db_session: Session,
) -> Dict[str, str] | None:

    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
    }

    data = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': _build_frontend_linear_redirect(),
        'prompt': 'consent',
        'client_id': LINEAR_CLIENT_ID,
        'client_secret': LINEAR_CLIENT_SECRET,
    }

    response = requests.post(f"{API_BASE_URL}/oauth/token", headers=headers, data=data)

    if response.status_code == 200:
        creds = response.json()

        new_creds_dict = {DB_CREDENTIALS_DICT_KEY: creds["access_token"]}

        if not update_credential_json(
            credential_id, 
            new_creds_dict,
            organization_id,
            user,
            db_session,
        ):
            return None
        return creds
    else:
        logger.exception(f"Failed to update Linear access token due to: {response.text}")
        return None