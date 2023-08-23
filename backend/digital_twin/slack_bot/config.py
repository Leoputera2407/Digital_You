from logging import Logger
from typing import Optional, Tuple
from uuid import UUID, uuid4

from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store import Bot, Installation
from slack_sdk.oauth.installation_store.async_installation_store import AsyncInstallationStore
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, WEB_DOMAIN
from digital_twin.config.constants import SLACK_APP_PERMISSIONS, SLACK_USER_SCOPES
from digital_twin.db.async_slack_bot import (
    async_consume_slack_state,
    async_find_bot_db,
    async_issue_slack_state,
    async_save_slack_bot,
    async_save_slack_installation,
    find_bot_db,
)
from digital_twin.db.engine import get_async_session, get_session
from digital_twin.db.model import SlackIntegration
from digital_twin.utils.logging import setup_logger

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

    async def async_save(
        self,
        installation: Installation,
        prosona_org_id: UUID,
        db_session: AsyncSession,
    ):
        try:
            await async_save_slack_installation(
                db_session,
                installation,
                prosona_org_id=prosona_org_id,
                client_id=self.client_id,
            )
            await async_save_slack_bot(
                db_session,
                installation,
                prosona_org_id=prosona_org_id,
                client_id=self.client_id,
            )
        except Exception as e:
            message = f"Failed to save installation: {installation} - {e}"
            self.logger.warning(message)

    async def async_find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        if is_enterprise_install or team_id is None:
            team_id = ""
        try:
            logger.info(f"Finding bot for team_id {team_id}")
            async with get_async_session(pool_pre_ping=True) as db_session:
                logger.info(f"We're in the async")
                bot = await async_find_bot_db(
                    db_session,
                    enterprise_id,
                    team_id,
                )
                logger.info(f"Found bot: {bot.team_id if bot else None}")
            if bot is None:
                message = f"Failed to find bot: {enterprise_id}, {team_id}, {is_enterprise_install}"
                return None
            return bot
        except Exception as e:
            message = f"Failed to find bot: {enterprise_id}, {team_id}, {is_enterprise_install} - {e}"
            self.logger.warning(message)
            return None


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

    async def async_issue(
        self,
        prosona_user_id: UUID,
        prosona_org_id: UUID,
        slack_integration_type: SlackIntegration,
        db_session: AsyncSession,
    ) -> str:
        state: str = str(uuid4())
        try:
            await async_issue_slack_state(
                db_session,
                state,
                prosona_user_id=prosona_user_id,
                prosona_org_id=prosona_org_id,
                slack_integration_type=slack_integration_type,
                expiration_seconds=120,
            )
        except Exception as e:
            message = f"Failed to issue a state: {state} - {e}"
            self.logger.warning(message)

        return state

    async def async_consume(
        self, state: str, db_session: AsyncSession
    ) -> Tuple[Optional[str], Optional[UUID], Optional[UUID], Optional[SlackIntegration]] | None:
        try:
            (
                state,
                prosona_org_id,
                prosona_user_id,
                slack_integration_type,
            ) = await async_consume_slack_state(
                db_session,
                state,
            )
            return state, prosona_org_id, prosona_user_id, slack_integration_type
        except Exception as e:
            message = f"Failed to find any persistent data for state: {state} - {e}"
            self.logger.warning(message)
            return None, None, None, None


def get_oauth_settings():
    return AsyncOAuthSettings(
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
        scopes=SLACK_APP_PERMISSIONS,
        user_scopes=SLACK_USER_SCOPES,
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
        success_url=f"{WEB_DOMAIN.rstrip('/')}/slack/settings",
        logger=logger,
    )
