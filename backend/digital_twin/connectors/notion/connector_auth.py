import json
import requests
import base64
import urllib.parse
from typing import Dict
from sqlalchemy.orm import Session

from digital_twin.config.app_config import (
    WEB_DOMAIN,
    NOTION_CLIENT_ID, 
    NOTION_CLIENT_SECRET,
)
from digital_twin.db.model import User
from digital_twin.db.connectors.credentials import update_credential_json
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

DB_CREDENTIALS_DICT_KEY = "notion_access_tokens"
BASE_URL = "https://api.notion.com"


def _build_frontend_notion_redirect() -> str:
    #return f"{WEB_DOMAIN}/connectors/notion/auth/callback"
    # TODO: Remove once done testing
    return f"{WEB_DOMAIN}/settings/connectors/notion/auth/callback"


def get_auth_url() -> str:
    params = {
        "client_id": NOTION_CLIENT_ID,
        "redirect_uri": _build_frontend_notion_redirect(),
        "response_type": "code",
    }

    auth_url = f"{BASE_URL}/v1/oauth/authorize?{urllib.parse.urlencode(params)}"

    
    return auth_url

def update_credential_access_tokens(
    auth_code: str,
    credential_id: int,
    user: User,
    db_session: Session,
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
        new_creds_dict = {DB_CREDENTIALS_DICT_KEY: json.dumps(creds)}

        if not update_credential_json(
            credential_id, 
            new_creds_dict,
            user,
            db_session,
        ):
            return None
        return creds
    else:
        logger.exception(f"Failed to update notion access token due to: {response.text}")
        return None