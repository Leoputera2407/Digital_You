from typing import List, Optional

from digital_twin.utils.clients import get_supabase_client
from digital_twin.utils.logging import setup_logger, log_supabase_api_error
from digital_twin.db.model import APIKey, ModelConfig
from digital_twin.server.model import APIKeyBase, BaseModelConfig

logger = setup_logger()

@log_supabase_api_error(logger)
