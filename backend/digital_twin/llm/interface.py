from pydantic import BaseModel
from postgrest.exceptions import APIError

from digital_twin.config.app_config import DEFAULT_LLM
from digital_twin.config.model_config import ModelInfo, SupportedModelType
from digital_twin.utils.clients import get_supabase_client


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
    try:
        response = get_supabase_client().table('model_config').select('*').eq("user_id", supabase_user_id).single().execute()
    except APIError as e:
        raise Exception(e.message)
    
    if not response.data:
        # TODO: Probably raise an error here
        model_config = SelectedModelConfig(
            model_info=SupportedModelType[DEFAULT_LLM].value,
        )
    else:
        data = response.data
        model_enum = SupportedModelType[data['supported_model_enum']]
        temperature = data['temperature'] if 'temperature' in data else 1.0

        model_config = SelectedModelConfig(
            model_info=model_enum.value,
            temperature=temperature
        )
        
    return model_config



