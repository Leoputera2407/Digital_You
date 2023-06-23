from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.db.model import APIKey, ModelConfig, User, DBAPIKeyType, SlackUser
from digital_twin.server.model import APIKeyBase, BaseModelConfig
from digital_twin.utils.logging import log_sqlalchemy_error, setup_logger, async_log_sqlalchemy_error


logger = setup_logger()

def mask_api_key(sensitive_str: str) -> str:
    return sensitive_str[:4] + "***...***" + sensitive_str[-4:]

@log_sqlalchemy_error(logger)
def upsert_api_key(user: User, api_key: APIKeyBase, db_session: Session) -> Optional[APIKey]:
    stmt = update(APIKey).where(APIKey.user_id == user.id, APIKey.key_type == api_key.key_type).values(**api_key.dict())
    db_session.execute(stmt)

    updated_api_key = db_session.execute(select(APIKey).where(APIKey.user_id == user.id, APIKey.key_type == api_key.key_type)).scalar_one()
    return updated_api_key

@log_sqlalchemy_error(logger)
def get_db_api_key(
    db_session: Session,
    user: Optional[User] = None,
    key_type: Optional[DBAPIKeyType] = None
) -> List[APIKey]:
    if not user:
        return []
    stmt = select(APIKey)
    if key_type:
        stmt = stmt.where(APIKey.user_id == user.id, APIKey.key_type == key_type)
    api_keys = db_session.execute(stmt).scalars().all()
    return api_keys

@async_log_sqlalchemy_error(logger)
async def async_get_db_api_key_for_slack_user(
    db_session: AsyncSession, 
    slack_user: Optional[SlackUser] = None, 
    key_type: Optional[DBAPIKeyType] = None
) -> List[APIKey]:
    if not slack_user:
        return []
    stmt = (
        select(APIKey)
        .join(User, APIKey.user_id == User.id)
        .join(SlackUser, User.id == SlackUser.user_id)
        .where(SlackUser.id == slack_user.id)
    )
    
    if key_type:
        stmt = stmt.where(APIKey.key_type == key_type)

    result = await db_session.execute(stmt)
    api_keys = result.scalars().all()
    
    return api_keys

@log_sqlalchemy_error(logger)
def delete_api_key(user: User, key_type: DBAPIKeyType, db_session: Session) -> bool:
    stmt = delete(APIKey).where(APIKey.user_id == user.id, APIKey.key_type == key_type)
    result = db_session.execute(stmt)
    db_session.commit()
    return result.rowcount > 0

@log_sqlalchemy_error(logger)
def upsert_model_config(user: User, model_config: BaseModelConfig, db_session: Session) -> Optional[ModelConfig]:
    stmt = update(ModelConfig).where(ModelConfig.user_id == user.id).values(**model_config.dict())
    db_session.execute(stmt)
    
    updated_model_config = db_session.execute(select(ModelConfig).where(ModelConfig.user_id == user.id)).scalar_one()
    return updated_model_config

@log_sqlalchemy_error(logger)
def get_model_config_by_user(
    db_session: Session, 
    user: Optional[User] = None
) -> Optional[ModelConfig]:
    if not user:
        return None
    model_config = db_session.execute(select(ModelConfig).where(ModelConfig.user_id == user.id)).scalar_one_or_none()
    return model_config

@async_log_sqlalchemy_error(logger)
async def async_get_model_config_by_slack_user(
    async_session: AsyncSession,
    slack_user: Optional[SlackUser] = None,
) -> Optional[ModelConfig]:
    if not slack_user:
        return None
    model_config = await async_session.execute(
        select(ModelConfig)
        .join(User, ModelConfig.user_id == User.id)
        .join(SlackUser, User.id == SlackUser.user_id)
        .where(SlackUser.id == slack_user.id)
    )
    return model_config.scalars().first()

# This mostly for testing purposes, don't expose to the API
@log_sqlalchemy_error(logger)
def delete_model_config(user: User, model_id: str, db_session: Session) -> bool:
    stmt = delete(ModelConfig).where(ModelConfig.user_id == user.id, ModelConfig.id == model_id)
    result = db_session.execute(stmt)
    db_session.commit()
    return result.rowcount > 0
