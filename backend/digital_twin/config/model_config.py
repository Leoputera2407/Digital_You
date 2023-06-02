from pydantic import BaseModel, Field
from enum import Enum


class ModelInfo(BaseModel):
    name: str
    n_context_len: int
    platform: str = Field(default="openai")


class SupportedModelType(Enum):
    GPT3_5 = ModelInfo(name="gpt-3.5-turbo", n_context_len=4096)
    GPT4 = ModelInfo(name="gpt-4", n_context_len=8192)
    ANTHROPIC = ModelInfo(name="claude", n_context_len=100000, platform="anthropic")

    @property
    def name(self):
        return self.value.name

    @property
    def n_context_len(self):
        return self.value.n_context_len
    
    @property
    def platform(self):
        return self.value.platform

map_model_platform_to_db_api_key_type = {
    "openai": "openai_api_key", 
    "anthropic": "anthropic_api_key"
}
