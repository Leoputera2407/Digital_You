from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.model import (
    SlackUser, 
    User, 
    UserOrganizationAssociation,
    Organization,
    Invitation,
)
from digital_twin.utils.logging import (
    setup_logger, 
    log_sqlalchemy_error,
    async_log_sqlalchemy_error,
)


logger = setup_logger()

@log_sqlalchemy_error(logger)
def get_user_org_by_user_and_org_id(
        session: Session, 
        user_id: UUID,
        organization_id: UUID
) -> Optional[UserOrganizationAssociation]:
    return session.query(
        UserOrganizationAssociation
    ).filter(
        UserOrganizationAssociation.user_id == user_id, 
        UserOrganizationAssociation.organization_id == organization_id
    ).first()

@async_log_sqlalchemy_error(logger)
async def async_get_user_org_by_user_and_org_id(
        session: AsyncSession, 
        user_id: UUID,
        organization_id: UUID
) -> Optional[UserOrganizationAssociation]:
    result = await session.execute(
        select(UserOrganizationAssociation)
        .where(
            and_(
                UserOrganizationAssociation.user_id == user_id, 
                UserOrganizationAssociation.organization_id == organization_id
            )
        )
    )
    return result.scalars().first()

@log_sqlalchemy_error(logger)
def get_organization_by_id(
    session: Session, 
    organization_id: UUID
) -> Optional[Organization]:
    return session.query(
            Organization
        ).filter(
            Organization.id == organization_id
        ).first()

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

@log_sqlalchemy_error(logger)
def get_user_org_assocations(
    user: User,
    db_session: Session,
) -> List[UserOrganizationAssociation]:
    result = db_session.execute(
        select(UserOrganizationAssociation)
        .where(UserOrganizationAssociation.user_id == user.id)
    )
    
    associations = result.scalars().all()

    if not associations:
        return []

    return associations


@async_log_sqlalchemy_error(logger)
async def async_get_user_org_assocations(
    user: User,
    db_session: AsyncSession,
) -> List[Organization]:
    result = await db_session.execute(
        select(UserOrganizationAssociation)
        .where(UserOrganizationAssociation.user_id == user.id)
    )
    
    associations = result.scalars().all()

    if not associations:
        return []    
    
    return associations

@log_sqlalchemy_error(logger)
def is_user_in_organization(
    session: Session, 
    user_email: str, 
    organization_id: UUID
) -> bool:
    user = get_user_by_email(session, user_email)
    if not user:
        return False

    user_org_association = session.query(
        UserOrganizationAssociation
    ).filter(
        UserOrganizationAssociation.user_id == user.id, 
        UserOrganizationAssociation.organization_id == organization_id
    ).first()

    return user_org_association is not None

def get_invitation_by_user_and_org(
    db_session: Session, 
    user_email: str,
    organization_id: UUID
) -> Optional[Invitation]:
    
    invitation = db_session.query(Invitation).filter(
        Invitation.invitee_email == user_email,
        Invitation.organization_id == organization_id
    ).first()

    return invitation

@async_log_sqlalchemy_error(logger)
async def async_get_slack_user(
    session: AsyncSession,
    slack_id: str, 
    team_id: str
) -> Optional[SlackUser]:
    result = await session.execute(
        select(SlackUser)
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
    organization_id: UUID,
    db_user_id: UUID
) -> Optional[SlackUser]:
    slack_user = SlackUser(
        slack_user_id=slack_user_id,
        team_id=team_id,
        organization_id=organization_id,
        user_id=db_user_id
    )
    session.add(slack_user)
    session.commit()
    return slack_user

@async_log_sqlalchemy_error(logger)
async def async_insert_slack_user(
    session: AsyncSession, 
    slack_user_id: str, 
    team_id: str, 
    organization_id: UUID,
    db_user_id: UUID
) -> Optional[SlackUser]:
    slack_user = SlackUser(
        slack_user_id=slack_user_id,
        team_id=team_id,
        organization_id=organization_id,
        user_id=db_user_id
    )
    session.add(slack_user)
    await session.commit()
    await session.refresh(slack_user)
    return slack_user


@log_sqlalchemy_error(logger)
def get_qdrant_collection_by_user_id(
    session: Session, 
    user_id: UUID,
    organization_id: UUID
) -> Optional[str]:
    user_org = get_user_org_by_user_and_org_id(
        session, 
        user_id,
        organization_id
    )
    if user_org and user_org.organization:
        return user_org.organization.get_qdrant_collection_key_str()
    else:
        return None

@log_sqlalchemy_error(logger)
def get_typesense_collection_by_user_id(
    session: Session, 
    user_id: UUID,
    organization_id: UUID,
) -> Optional[str]:
    user_org = get_user_org_by_user_and_org_id(
        session, 
        user_id,
        organization_id
    )
    if user_org and user_org.organization:
        return user_org.organization.get_typesense_collection_key_str()
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
    
    if slack_user and slack_user.organization:
        return slack_user.organization.get_qdrant_collection_key_str()
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
    
    if slack_user and slack_user.organization:
        return slack_user.organization.get_typesense_collection_key_str()
    else:
        return None
