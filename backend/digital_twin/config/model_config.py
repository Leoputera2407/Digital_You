from enum import Enum

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    n_context_len: int
    platform: str = Field(default="openai")


class SupportedModelType(Enum):
    GPT3_5 = ModelInfo(name="gpt-3.5-turbo", n_context_len=4096)
    GPT3_5_FN = ModelInfo(name="gpt-3.5-turbo-0613", n_context_len=4096)
    GPT4 = ModelInfo(name="gpt-4", n_context_len=8192)
    GPT3_5_16k = ModelInfo(name="gpt-3.5-turbo-16k", n_context_len=16384)
    GPT3_5_16k_FN = ModelInfo(name="gpt-3.5-turbo-16k-0613", n_context_len=16384)
    ANTHROPIC = ModelInfo(name="claude", n_context_len=100000, platform="anthropic")
    AZURE = ModelInfo(name="azure", n_context_len=4096, platform="azure")

    @property
    def name(self):
        return self.value.name

    @property
    def n_context_len(self):
        return self.value.n_context_len

    @property
    def platform(self):
        return self.value.platform
