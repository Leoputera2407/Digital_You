from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from digital_twin.config.app_config import DEFAULT_LLM
from digital_twin.config.model_config import ModelInfo, SupportedModelType
from digital_twin.db.llm import get_model_config_by_user, async_get_model_config_by_slack_user
from digital_twin.db.model import User

from digital_twin.utils.logging import setup_logger

logger = setup_logger()

class SelectedModelConfig(BaseModel):
    model_info: ModelInfo
    temperature: float = 0.0

    @property
    def name(self):
        return self.model_info.name

    @property
    def n_context_len(self):
        return self.model_info.n_context_len
    
    @property
    def platform(self):
        return self.model_info.platform

    @property 
    def temperature(self):
        return self.temperature


def get_selected_model_config(db_session: Session, user: Optional[User]=None) -> SelectedModelConfig:
    model_config = get_model_config_by_user(user, db_session)
    if not model_config:
        logger.info("No model config found for user, using default model config")
        model_config = SelectedModelConfig(
            model_info=SupportedModelType[DEFAULT_LLM].value,
        )
    else:
        model_enum = SupportedModelType[model_config.supported_model_enum]
        temperature = model_config.temperature
        model_config = SelectedModelConfig(
            model_info=model_enum.value,
            temperature=temperature
        )
        
    return model_config


async def async_get_selected_model_config(db_session: AsyncSession, user: Optional[User] = None) -> SelectedModelConfig:
    model_config = await async_get_model_config_by_slack_user(user, db_session)
    if not model_config:
        logger.info("No model config found for user, using default model config")
        model_config = SelectedModelConfig(
            model_info=SupportedModelType[DEFAULT_LLM].value,
        )
    else:
        model_enum = SupportedModelType[model_config.supported_model_enum]
        temperature = model_config.temperature
        model_config = SelectedModelConfig(
            model_info=model_enum.value,
            temperature=temperature
        )
        
    return model_config
