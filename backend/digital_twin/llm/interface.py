from pydantic import BaseModel
from postgrest.exceptions import APIError

from digital_twin.config.app_config import DEFAULT_LLM
from digital_twin.config.model_config import ModelInfo, SupportedModelType
from digital_twin.db.llm import get_model_config_by_user

class SelectedModelConfig(BaseModel):
    model_info: ModelInfo
    temperature: float = 1.0

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


def get_selected_model_config(supabase_user_id: str) -> SelectedModelConfig:
    model_config = get_model_config_by_user(supabase_user_id)
    if not model_config:
        # TODO: Probably raise an error here
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

