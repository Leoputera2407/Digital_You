from digital_twin.config.app_config import OPENAI_API_KEY
from digital_twin.db.llm import get_db_api_key
from digital_twin.db.model import map_platform_to_db_api_key_type
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def get_api_key(supabase_user_id: str, platform: str) -> str:
    db_api_key_type = map_platform_to_db_api_key_type[platform]
    model_config_list = get_db_api_key(user_id=supabase_user_id, key_type=db_api_key_type)
    if not model_config_list:
        logger.error(f'No API key found for user {supabase_user_id} on platform {platform}')
    return model_config_list[0].key_value if model_config_list else OPENAI_API_KEY
