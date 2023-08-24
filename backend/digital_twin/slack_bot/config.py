from datetime import datetime
from logging import Logger
from typing import Mapping, Optional, Tuple, Union
from uuid import UUID, uuid4

from redis import asyncio as aioredis
from redis.asyncio.client import Redis
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store import Bot, Installation
from slack_sdk.oauth.installation_store.async_installation_store import AsyncInstallationStore
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import (
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    WEB_DOMAIN,
)
from digital_twin.config.constants import SLACK_APP_PERMISSIONS, SLACK_USER_SCOPES
from digital_twin.db.async_slack_bot import (
    async_consume_slack_state,
    async_issue_slack_state,
    async_save_slack_bot,
    async_save_slack_installation,
)
from digital_twin.db.model import SlackBots, SlackIntegration
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

HSET_TYPE = Mapping[Union[str, bytes], Union[bytes, float, int, str]]


class AsyncHackyRedisInstallationStore(AsyncInstallationStore):
    def __init__(self, logger):
        self._logger = logger

    async def async_save_to_redis(self, installation: Installation) -> None:
        redis: Redis = await aioredis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            ssl=True,
        )
        try:
            # Serialize and save installation
            serialized_installation_dict = self._serialize_installation(installation)
            team_id = (
                serialized_installation_dict["team_id"].decode("utf-8")
                if isinstance(serialized_installation_dict["team_id"], bytes)
                else serialized_installation_dict["team_id"]
            )
            enterprise_id = (
                serialized_installation_dict["enterprise_id"].decode("utf-8")
                if isinstance(serialized_installation_dict["enterprise_id"], bytes)
                else serialized_installation_dict["enterprise_id"]
            )
            installed_at = (
                serialized_installation_dict["installed_at"].decode("utf-8")
                if isinstance(serialized_installation_dict["installed_at"], bytes)
                else serialized_installation_dict["installed_at"]
            )
            installation_key = f"slack_installation:{team_id}:{enterprise_id}:{installed_at}"
            await redis.hmset(installation_key, serialized_installation_dict)

            # Serialize and save bot
            serialized_bot_dict = self._serialize_bot(installation)
            team_id = (
                serialized_bot_dict["team_id"].decode("utf-8")
                if isinstance(serialized_bot_dict["team_id"], bytes)
                else serialized_bot_dict["team_id"]
            )
            enterprise_id = (
                serialized_bot_dict["enterprise_id"].decode("utf-8")
                if isinstance(serialized_bot_dict["enterprise_id"], bytes)
                else serialized_bot_dict["enterprise_id"]
            )
            installed_at = (
                serialized_bot_dict["installed_at"].decode("utf-8")
                if isinstance(serialized_bot_dict["installed_at"], bytes)
                else serialized_bot_dict["installed_at"]
            )
            bot_key = f"slack_bot:{team_id}:{enterprise_id}:{installed_at}"
            await redis.hmset(bot_key, serialized_bot_dict)

        except Exception as e:
            self._logger.warning(f"Failed to save installation: {installation} - {e}")
        finally:
            await redis.close()

    async def async_find_bot_redis(
        self, enterprise_id: Optional[str] = None, team_id: Optional[str] = None
    ) -> Optional[Bot]:
        redis: Redis = await aioredis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            ssl=True,
        )
        try:
            enterprise_id_str = enterprise_id or ""

            # If both enterprise_id and team_id are provided, get the specific keys
            all_keys = await redis.keys(f"slack_bot:{team_id}:{enterprise_id_str}:*")

            bots = []
            for key in all_keys:
                bot_data = await redis.hgetall(key)
                bots.append(bot_data)

            # Sort by installed_at and take the latest
            if bots:
                latest_bot_data = sorted(
                    bots, key=lambda x: x[b"installed_at"].decode("utf-8"), reverse=True
                )[0]
                return self._deserialize_bot(latest_bot_data)
            else:
                return None
        except Exception as e:
            self._logger.warning(f"Failed to get bot for team_id: {team_id} - {e}")
            return None
        finally:
            await redis.close()

    def _serialize_installation(self, installation: Installation) -> HSET_TYPE:
        installation_dict: HSET_TYPE = {
            "app_id": installation.app_id,
            "enterprise_id": installation.enterprise_id or "",
            "enterprise_name": installation.enterprise_name or "",
            "enterprise_url": installation.enterprise_url or "",
            "team_id": installation.team_id,
            "team_name": installation.team_name or "",
            "bot_token": installation.bot_token or "",
            "bot_id": installation.bot_id,
            "bot_user_id": installation.bot_user_id,
            "bot_scopes": ",".join(installation.bot_scopes),
            "bot_refresh_token": installation.bot_refresh_token or "",
            "bot_token_expires_at": str(installation.bot_token_expires_at)
            if installation.bot_token_expires_at
            else "",
            "user_id": installation.user_id,
            "user_token": installation.user_token or "",
            "user_scopes": ",".join(installation.user_scopes),
            "user_refresh_token": installation.user_refresh_token or "",
            "user_token_expires_at": str(installation.user_token_expires_at)
            if installation.user_token_expires_at
            else "",
            "incoming_webhook_url": installation.incoming_webhook_url or "",
            "incoming_webhook_channel": installation.incoming_webhook_channel or "",
            "incoming_webhook_channel_id": installation.incoming_webhook_channel_id or "",
            "incoming_webhook_configuration_url": installation.incoming_webhook_configuration_url or "",
            "is_enterprise_install": str(installation.is_enterprise_install),
            "token_type": installation.token_type or "",
            "installed_at": str(installation.installed_at),
        }
        return installation_dict

    def _serialize_bot(self, bot: Bot) -> HSET_TYPE:
        bot_dict: HSET_TYPE = {
            "enterprise_id": bot.enterprise_id or "",
            "enterprise_name": bot.enterprise_name or "",
            "team_id": bot.team_id,
            "team_name": bot.team_name or "",
            "bot_token": bot.bot_token,
            "bot_id": bot.bot_id,
            "bot_user_id": bot.bot_user_id,
            "bot_scopes": ",".join(bot.bot_scopes),
            "bot_refresh_token": bot.bot_refresh_token or "",
            "bot_token_expires_at": str(bot.bot_token_expires_at) if bot.bot_token_expires_at else "",
            "is_enterprise_install": str(bot.is_enterprise_install),
            "installed_at": str(bot.installed_at),
        }
        return bot_dict

    def _deserialize_bot(self, data: dict[bytes, bytes]) -> Bot:
        return Bot(
            app_id=data.get(b"app_id", b"").decode("utf-8"),
            enterprise_id=data.get(b"enterprise_id", b"").decode("utf-8") or None,
            enterprise_name=data.get(b"enterprise_name", b"").decode("utf-8") or None,
            team_id=data[b"team_id"].decode("utf-8"),
            team_name=data.get(b"team_name", b"").decode("utf-8") or None,
            bot_token=data[b"bot_token"].decode("utf-8"),
            bot_id=data[b"bot_id"].decode("utf-8"),
            bot_user_id=data[b"bot_user_id"].decode("utf-8"),
            bot_scopes=data[b"bot_scopes"].decode("utf-8").split(","),
            bot_refresh_token=data.get(b"bot_refresh_token", b"").decode("utf-8") or None,
            bot_token_expires_at=(
                datetime.fromtimestamp(float(data[b"bot_token_expires_at"].decode("utf-8")))
                if b"bot_token_expires_at" in data and data[b"bot_token_expires_at"].decode("utf-8").strip()
                else None
            ),
            is_enterprise_install=(
                bool(data[b"is_enterprise_install"])
                if b"is_enterprise_install" in data and data[b"is_enterprise_install"].decode("utf-8").strip()
                else None
            ),
            installed_at=(
                datetime.fromtimestamp(float(data[b"installed_at"].decode("utf-8")))
                if b"installed_at" in data and data[b"installed_at"].decode("utf-8").strip()
                else None
            ),
        )


class AsyncSQLAlchemyInstallationStore(AsyncInstallationStore):
    client_id: str

    def __init__(
        self,
        client_id: str,
        redis_hack_store: AsyncHackyRedisInstallationStore,
        logger: Logger = logger,
    ):
        self.client_id = client_id
        self.redis_hack_store = redis_hack_store
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
            await self.redis_hack_store.async_save_to_redis(installation=installation)

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
            bot = await self.redis_hack_store.async_find_bot_redis(
                enterprise_id=enterprise_id,
                team_id=team_id,
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
            redis_hack_store=AsyncHackyRedisInstallationStore(
                logger=logger,
            ),
            logger=logger,
        ),
        state_store=AsyncSQLAlchemyOAuthStateStore(
            expiration_seconds=120,
            logger=logger,
        ),
        success_url=f"{WEB_DOMAIN.rstrip('/')}/slack/settings",
        logger=logger,
    )
