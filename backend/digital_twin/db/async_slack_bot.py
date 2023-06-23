import time
from typing import List, Optional, Tuple
from datetime import datetime

import ast

from slack_sdk.oauth.installation_store import Bot, Installation
from sqlalchemy import and_, desc, Table, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.utils.logging import setup_logger, log_sqlalchemy_error
from digital_twin.db.model import SlackUser

logger = setup_logger()

@log_sqlalchemy_error(logger)
async def async_find_bot(
    session: AsyncSession,
    bots_table: Table,
    enterprise_id: Optional[str],
    team_id: Optional[str],
    is_enterprise_install: Optional[bool],
) -> Optional[Bot]:
    try:
        c = bots_table.c
        query = bots_table.select().where(
            and_(
                c.enterprise_id == enterprise_id,
                c.team_id == team_id,
                c.is_enterprise_install == is_enterprise_install,
            )
        ).order_by(desc(c.installed_at)).limit(1)

        result = await session.execute(query)
        bot = result.fetchone()

        if bot:
            return Bot(
                app_id=bot["app_id"],
                enterprise_id=bot["enterprise_id"],
                team_id=bot["team_id"],
                bot_token=bot["bot_token"],
                bot_id=bot["bot_id"],
                bot_user_id=bot["bot_user_id"],
                bot_scopes=bot["bot_scopes"],
                installed_at=bot["installed_at"],
            )
        else:
            return None
    except Exception as e:
        logger.error(f"Error in async_find_bot: {e}")
        return None

@log_sqlalchemy_error(logger)
async def async_save_slack_installation(
    session: AsyncSession,
    installations_table: Table,
    installation: Installation,
    client_id: str
) -> bool:
    try:
        i = installation.to_dict()
        i["client_id"] = client_id
        await session.execute(installations_table.insert(), i)
        return True
    except:
        return False
    
@log_sqlalchemy_error(logger)
async def async_save_slack_bot(
    session: AsyncSession,
    bots_table: Table,
    installation: Installation,
    client_id: str
) -> bool:
    try:
        b = installation.to_bot().to_dict()
        b["client_id"] = client_id
        await session.execute(bots_table.insert(), b)
        return True
    except:
        return False

@log_sqlalchemy_error(logger)
async def async_issue_slack_state(
    session: AsyncSession, 
    oauth_states_table: Table, 
    state: str, 
    expiration_seconds: int
) -> bool:
    try:
        now = datetime.utcfromtimestamp(time.time() + expiration_seconds)
        await session.execute(oauth_states_table.insert(), {"state": state, "expire_at": now})
        return True
    except:
        return False

@log_sqlalchemy_error(logger)
async def async_consume_slack_state(
    session: AsyncSession, 
    oauth_states_table: Table, 
    state: str
) -> bool:
    try:
        c = oauth_states_table.c
        query = oauth_states_table.select().where(
            and_(c.state == state, c.expire_at > datetime.utcnow()))
        result = await session.execute(query)
        row = result.fetchone()
        logger.debug(f"consume's query result: {row}")
        if row:
            await session.execute(oauth_states_table.delete().where(c.id == row["id"]))
            return True
        else:
            logger.warning(f"No state found to consume: {state}")
            return False
    except:
        return False

@log_sqlalchemy_error(logger)
async def async_get_convo_style(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str
) -> Optional[str]:
    result = await session.execute(
        select(SlackUser.conversation_style).where(
            SlackUser.slack_user_id == slack_user_id, 
            SlackUser.team_id == team_id
        )
    )
    slack_user: SlackUser = result.scalars().first()
    return slack_user.conversation_style if slack_user else None

@log_sqlalchemy_error(logger)
async def async_update_convo_style(
    session: AsyncSession, 
    personality_description: str,
    slack_user_id: str,
    team_id: str
) -> Optional[SlackUser]:
    try:
        result = await session.execute(
            select(SlackUser).where(
                SlackUser.slack_user_id == slack_user_id, 
                SlackUser.team_id == team_id
            )
        )
        slack_user = result.scalars().first()
        if slack_user:
            slack_user.conversation_style = personality_description
            await session.commit()
        return slack_user
    except Exception as e:
        logger.error(f"Failed to update conversation style: {e}")
        return None

@log_sqlalchemy_error(logger)
async def async_update_chat_pairs(
    session: AsyncSession, 
    chat_transcript: str, 
    chat_pairs: List[Tuple[str, str]], 
    slack_user_id: str, 
    team_id: str
) -> Optional[SlackUser]:
    try:
        result = await session.execute(
            select(SlackUser).where(
                SlackUser.slack_user_id == slack_user_id, 
                SlackUser.team_id == team_id
            )
        )
        slack_user = result.scalars().first()
        if slack_user:
            slack_user.contiguous_chat_transcript = chat_transcript
            slack_user.chat_pairs = str(chat_pairs)  # Convert list to string
            await session.commit()
        return slack_user
    except Exception as e:
        logger.error(f"Failed to update chat pairs: {e}")
        return None

@log_sqlalchemy_error(logger)
async def async_get_chat_pairs(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str
) -> List[Tuple[str, str]]:
    result = await session.execute(
        select(SlackUser.chat_pairs).where(
            SlackUser.slack_user_id == slack_user_id, 
            SlackUser.team_id == team_id
        )
    )
    slack_user: SlackUser  = result.scalars().first()
    return ast.literal_eval(slack_user.chat_pairs) if slack_user and slack_user.chat_pairs else []
