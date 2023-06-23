from typing import Optional
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.db.llm import get_db_api_key, async_get_db_api_key
from digital_twin.db.model import map_platform_to_db_api_key_type, User
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def get_api_key(
        db_session: Session,
        platform: str,
        user: Optional[User]= None, 
) -> str:
    """
    Get DB API Keys or if not found, return the default API key
    """
    db_api_key_type = map_platform_to_db_api_key_type[platform]
    api_key_list = get_db_api_key(db_session, user=user, key_type=db_api_key_type)
    if not api_key_list:
        logger.error(f'No API key found for user {user.id} on platform {platform}')
    return api_key_list[0].key_value if api_key_list else OPENAI_API_KEY

async def async_get_api_key(
        db_session: AsyncSession, 
        platform: str,
        user: Optional[User]= None, 
) -> str:
    """
    Get DB API Keys or if not found, return the default API key
    """
    db_api_key_type = map_platform_to_db_api_key_type[platform]
    api_key_list = await async_get_db_api_key(db_session, user=user, key_type=db_api_key_type)
    if not api_key_list:
        logger.error(f'No API key found for user {user.id} on platform {platform}')
    return api_key_list[0].key_value if api_key_list else OPENAI_API_KEY