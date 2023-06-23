from uuid import uuid4
from typing import Optional
from logging import Logger

from sqlalchemy import Table, MetaData

from slack_sdk.oauth.installation_store import Bot, Installation
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore


from digital_twin.config.app_config import (
    SLACK_CLIENT_ID, 
    SLACK_CLIENT_SECRET, 
)
from digital_twin.config.constants import SLACK_APP_PERMISSIONS

from digital_twin.utils.logging import setup_logger
from digital_twin.db.engine import get_async_session
from digital_twin.db.async_slack_bot import (
    async_save_slack_installation,
    async_save_slack_bot,
    async_find_bot,
    async_issue_slack_state,
    async_consume_slack_state,
)

logger = setup_logger()

class AsyncSQLAlchemyInstallationStore(AsyncInstallationStore):
    client_id: str

    def __init__(
        self,
        client_id: str,
        logger: Logger = logger,
    ):
        self.client_id = client_id
        self._logger = logger

    @property
    def logger(self) -> Logger:
        return self._logger

    async def async_save(self, installation: Installation):
        try:
            async with get_async_session() as async_session:
                await async_save_slack_installation(
                    async_session, installation, self.client_id
                )
                await async_save_slack_bot(
                    async_session, installation, self.client_id
                )
        except Exception as e:
            message = f"Failed to save installation: {installation} - {e}"
            self.logger.warning(message)
            
    async def async_find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool],
    ) -> Optional[Bot]:
        try:
            async with get_async_session() as async_session:
                bot = await async_find_bot(
                    async_session, enterprise_id, team_id, is_enterprise_install,
                )
        except Exception as e:
            message = f"Failed to find bot: {enterprise_id}, {team_id}, {is_enterprise_install} - {e}"
            self.logger.warning(message)
            return None
        return bot

class AsyncSQLAlchemyOAuthStateStore(AsyncOAuthStateStore):
    expiration_seconds: int

    def __init__(
        self,
        *,
        expiration_seconds: int,
        logger: Logger = logger,
    ):
        self.expiration_seconds = expiration_seconds
        self._logger = logger

    @property
    def logger(self) -> Logger:
        return self._logger

    async def async_issue(self) -> str:
        state: str = str(uuid4())
        try:
            async with get_async_session() as async_session:
                await async_issue_slack_state(
                    async_session, state, 120
                )
        except Exception as e:
            message = f"Failed to issue a state: {state} - {e}"
            self.logger.warning(message)

        return state

    async def async_consume(self, state: str) -> bool:
        try:
            async with get_async_session() as async_session:
                return await async_consume_slack_state(
                    async_session, state,
                )
        except Exception as e:
            message = f"Failed to find any persistent data for state: {state} - {e}"
            self.logger.warning(message)
            return False


def get_oauth_settings():
    return AsyncOAuthSettings(
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
        scopes=SLACK_APP_PERMISSIONS,
        install_page_rendering_enabled=True,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        installation_store=AsyncSQLAlchemyInstallationStore(
            client_id=SLACK_CLIENT_ID,
            logger=logger,
        ),
        state_store=AsyncSQLAlchemyOAuthStateStore(
            expiration_seconds=120,
            logger=logger,
        ),
        logger=logger,
    )