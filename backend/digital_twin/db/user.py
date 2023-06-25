from typing import Optional

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.model import SlackUser, User
from digital_twin.utils.logging import (
    setup_logger, 
    log_sqlalchemy_error,
    async_log_sqlalchemy_error,
)


logger = setup_logger()


@log_sqlalchemy_error(logger)
def get_user_by_id(
    session: Session, 
    user_id: UUID
) -> Optional[User]:
    user = session.query(User).filter(User.id == user_id).first()
    return user

@async_log_sqlalchemy_error(logger)
async def async_get_user_by_id(
    session: AsyncSession, 
    user_id: UUID
) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    return user


@log_sqlalchemy_error(logger)
def get_user_by_email(
    session: Session, 
    user_email: str
) -> Optional[User]:
    user = session.query(User).filter(User.email == user_email).first()
    return user


@async_log_sqlalchemy_error(logger)
async def async_get_user_by_email(
    session: AsyncSession, 
    user_email: str
) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == user_email))
    user = result.scalars().first()
    return user



@async_log_sqlalchemy_error(logger)
async def async_get_slack_user(
    session: AsyncSession,
    slack_id: str, 
    team_id: str
) -> Optional[SlackUser]:
    result = await session.execute(
        select(SlackUser).options(
            joinedload(SlackUser.user).joinedload(User.organization)
        )
        .where(
            SlackUser.slack_user_id == slack_id, 
            SlackUser.team_id == team_id
        )
    )
    return result.scalars().first()

@log_sqlalchemy_error(logger)
def insert_slack_user(
    session: Session, 
    slack_user_id: str, 
    team_id: str, 
    db_user_id: UUID
) -> Optional[SlackUser]:
    slack_user = SlackUser(
        slack_user_id=slack_user_id,
        team_id=team_id,
        user_id=db_user_id
    )
    session.add(slack_user)
    session.commit()
    return slack_user


@log_sqlalchemy_error(logger)
def get_qdrant_collection_by_user_id(session: Session, user_id: UUID) -> Optional[str]:
    user = get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.get_qdrant_collection_key_str()
    else:
        return None

@log_sqlalchemy_error(logger)
def get_typesense_collection_by_user_id(session: Session, user_id: UUID) -> Optional[str]:
    user = get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.get_typesense_collection_key_str()
    else:
        return None

@async_log_sqlalchemy_error(logger)
async def async_get_qdrant_collection_for_slack(
    session: AsyncSession, 
    slack_user_id: str,
    team_id: str,
) -> Optional[str]:
    slack_user = await async_get_slack_user(
        session, 
        slack_user_id,
        team_id
    )
    
    if slack_user and slack_user.user and slack_user.user.organization:
        return slack_user.user.organization.get_qdrant_collection_key_str()
    else:
        return None

@async_log_sqlalchemy_error(logger)
async def async_get_typesense_collection_for_slack(
    session: AsyncSession, 
    slack_user_id: str,
    team_id: str,
) -> Optional[str]:
    slack_user = await async_get_slack_user(
        session, 
        slack_user_id,
        team_id,
    )
    
    if slack_user and slack_user.user and slack_user.user.organization:
        return slack_user.user.organization.get_typesense_collection_key_str()
    else:
        return None
