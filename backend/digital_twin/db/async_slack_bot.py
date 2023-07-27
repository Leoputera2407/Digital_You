import time
from uuid import UUID
from typing import List, Optional, Tuple
from datetime import datetime

import ast

from slack_sdk.oauth.installation_store import Bot, Installation
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.utils.logging import setup_logger, async_log_sqlalchemy_error
from digital_twin.db.model import (
    SlackUser, 
    SlackBots, 
    SlackInstallations,
    SlackOAuthStates,
    SlackIntegration,
    SlackOrganizationAssociation,
)

logger = setup_logger()

@async_log_sqlalchemy_error(logger)
async def async_find_bot_db(
    session: AsyncSession,
    enterprise_id: Optional[str],
    team_id: Optional[str],
    is_enterprise_install: Optional[bool],
) -> Optional[Bot]:
    try:
        query = select(SlackBots).where(
            and_(
                SlackBots.enterprise_id == enterprise_id,
                SlackBots.team_id == team_id,
                SlackBots.is_enterprise_install == is_enterprise_install,
            )
        ).order_by(desc(SlackBots.installed_at)).limit(1)

        result = await session.execute(query)
        bot = result.fetchone()

        if bot:
            bot: SlackBots = bot[0] 
            return Bot(
                app_id=bot.app_id,
                enterprise_id=bot.enterprise_id,
                team_id=bot.team_id,
                bot_token=bot.bot_token,
                bot_id=bot.bot_id,
                bot_user_id=bot.bot_user_id,
                bot_scopes=bot.bot_scopes,
                installed_at=bot.installed_at,
            )
        else:
            return None
    except Exception as e:
        logger.error(f"Error in async_find_bot: {e}")
        return None

@async_log_sqlalchemy_error(logger)
async def async_save_slack_installation(
    session: AsyncSession,
    installation: Installation,
    prosona_org_id: UUID,
    client_id: str
) -> bool:
    i = installation.to_dict()
    i["client_id"] = client_id
    session.add(SlackInstallations(
        **i,
        prosona_organization_id=prosona_org_id
        )
    )
    await session.commit()
    return True
    
@async_log_sqlalchemy_error(logger)
async def async_save_slack_bot(
    session: AsyncSession,
    installation: Installation,
    prosona_org_id: UUID,
    client_id: str
) -> bool:
    b = installation.to_bot().to_dict()
    b["client_id"] = client_id
    session.add(SlackBots(
        **b,
        prosona_organization_id=prosona_org_id,
        )
    )
    await session.commit()
    return True

@async_log_sqlalchemy_error(logger)
async def async_issue_slack_state(
    session: AsyncSession, 
    state: str, 
    prosona_user_id: UUID,
    prosona_org_id: UUID,
    slack_integration_type: SlackIntegration,
    expiration_seconds: int
) -> bool:    
    now = datetime.utcfromtimestamp(time.time() + expiration_seconds)
    session.add(SlackOAuthStates(
        state=state, 
        expire_at=now,
        prosona_user_id=prosona_user_id,
        prosona_organization_id=prosona_org_id,
        slack_integration_type=slack_integration_type
        )
    )
    await session.commit()
    return True


@async_log_sqlalchemy_error(logger)
async def async_consume_slack_state(
    session: AsyncSession, 
    state: str
) -> Tuple[str, UUID, UUID, SlackIntegration]:
    """
    It returns the whether the state is valid and 
    the prosona_organization_id associated with the state.
    """
    query = select(SlackOAuthStates).where(
            and_(SlackOAuthStates.state == state, SlackOAuthStates.expire_at > datetime.utcnow()))
    result = await session.execute(query)
    slack_state_instance = result.scalars().first()
    if slack_state_instance:
        await session.delete(slack_state_instance)
        await session.commit()
        return slack_state_instance.state, slack_state_instance.prosona_organization_id, slack_state_instance.prosona_user_id, slack_state_instance.slack_integration_type
    else:
        logger.warning(f"No state found to consume: {state}")
        raise Exception(f"No state found to consume: {state}")
   
@async_log_sqlalchemy_error(logger)
async def async_get_convo_style_and_last_update_at(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str
) -> Tuple[Optional[str], Optional[datetime]]:
    result = await session.execute(
        select(SlackUser).where(
            SlackUser.slack_user_id == slack_user_id, 
            SlackUser.team_id == team_id
        )
    )
    slack_user = result.scalars().first()
    if slack_user is None:
        return None, None
    conversation_style, updated_at = slack_user.conversation_style, slack_user.updated_at
    return conversation_style, updated_at

@async_log_sqlalchemy_error(logger)
async def async_update_convo_style(
    session: AsyncSession, 
    personality_description: str,
    slack_user_id: str,
    team_id: str
) -> Optional[SlackUser]:
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

@async_log_sqlalchemy_error(logger)
async def async_update_chat_pairs(
    session: AsyncSession, 
    chat_transcript: Optional[List[str]], 
    chat_pairs: Optional[List[Tuple[str, str]]], 
    slack_user_id: str, 
    team_id: str
) -> Optional[SlackUser]:
    result = await session.execute(
        select(SlackUser).where(
            SlackUser.slack_user_id == slack_user_id, 
            SlackUser.team_id == team_id
        )
    )
    slack_user = result.scalars().first()
    if slack_user:
        slack_user.contiguous_chat_transcript = str(chat_transcript) if chat_transcript is not None else None
        slack_user.chat_pairs = str(chat_pairs) if chat_pairs is not None else None
        await session.commit()
    return slack_user

@async_log_sqlalchemy_error(logger)
async def async_get_chat_pairs(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str
) -> List[Tuple[str, str]]:
    chat_pairs = await session.execute(
        select(SlackUser.chat_pairs).where(
            SlackUser.slack_user_id == slack_user_id, 
            SlackUser.team_id == team_id
        )
    )
    chat_pair = chat_pairs.scalars().first()
    return ast.literal_eval(chat_pair) if chat_pair else []

@async_log_sqlalchemy_error(logger)
async def async_get_associated_slack_user(
    session: AsyncSession, 
    user_id: str, 
    organization_id: str
) -> Optional[SlackUser]:
    result = await session.execute(
        select(SlackUser).options(
            joinedload(SlackUser.slack_organization_association)
        ).where(
            SlackUser.user_id == user_id, 
            SlackUser.slack_organization_association.has(
                SlackOrganizationAssociation.organization_id == organization_id
            )
        )
    )
    return result.scalars().first()