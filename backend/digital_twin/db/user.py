from typing import Optional

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.model import SlackUser, User, Organization
from digital_twin.utils.logging import setup_logger, log_sqlalchemy_error


logger = setup_logger()


@log_sqlalchemy_error(logger)
def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    user = session.query(User).filter(User.id == user_id).first()
    return user

@log_sqlalchemy_error(logger)
async def async_get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    return user


@log_sqlalchemy_error(logger)
async def async_get_slack_user(session: AsyncSession, slack_id: str, team_id: str) -> Optional[SlackUser]:
    result = await session.execute(
        select(SlackUser)
        .where(
            SlackUser.slack_user_id == slack_id, 
            SlackUser.team_id == team_id
        )
    )
    return result.scalars().first()

@log_sqlalchemy_error(logger)
def insert_slack_user(session: Session, slack_user_id: str, team_id: str, db_user_id: int) -> Optional[SlackUser]:
    slack_user = SlackUser(
        slack_user_id=slack_user_id,
        team_id=team_id,
        user_id=db_user_id
    )
    session.add(slack_user)
    session.commit()
    return slack_user


@log_sqlalchemy_error(logger)
def get_qdrant_collection_by_user_id(session: Session, user_id: int) -> Optional[UUID]:
    user = get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.qdrant_collection_key
    else:
        return None

@log_sqlalchemy_error(logger)
def get_typesense_collection_by_user_id(session: Session, user_id: int) -> Optional[UUID]:
    user = get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.typesense_collection_key
    else:
        return None

@log_sqlalchemy_error(logger)
async def async_get_qdrant_collection_by_user_id(session: AsyncSession, user_id: int) -> Optional[UUID]:
    user = await async_get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.qdrant_collection_key
    else:
        return None

@log_sqlalchemy_error(logger)
async def async_get_typesense_collection_by_user_id(session: AsyncSession, user_id: int) -> Optional[UUID]:
    user = await async_get_user_by_id(session, user_id)
    if user and user.organization:
        return user.organization.typesense_collection_key
    else:
        return None

