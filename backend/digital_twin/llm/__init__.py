from typing import Optional

from langchain.llms.base import BaseLanguageModel

from digital_twin.config.model_config import map_model_platform_to_db_api_key_type
from digital_twin.llm.config import get_api_key
from digital_twin.llm.interface import SelectedModelConfig


def get_selected_llm_instance(
    user_id: str,
    model_config: SelectedModelConfig, **kwargs
) -> Optional[BaseLanguageModel]:
    llm: BaseLanguageModel = None
    api_key = get_api_key(
        user_id,
        model_config.platform,
    ).key_value
    if not api_key:
        raise ValueError("API key wasn't set for {model_config.platform}}")
   
    if model_config.name.startswith("gpt"):
        from langchain.chat_models import ChatOpenAI

        llm = ChatOpenAI(
            model_name=model_config.name,
            api_key=api_key,
            temperature=model_config.temperature,
            max_tokens=kwargs.get(
                "max_output_tokens", model_config.n_context_len
            ),
            streaming=False,
        )
    elif model_config.name.startswith("claude"):
        from langchain.chat_models import ChatAnthropic

        llm = ChatAnthropic(
            model=model_config.name,
            antrhopic_api_key=api_key,
            temperature=model_config.temperature,
            max_tokens_to_sample=kwargs.get(
                "max_output_tokens", model_config.n_context_len
            ),
            streaming=False,
        )
    else:
        raise ValueError(
            "Only OpenAI or Claude is supported right now. Make sure you set up your .env correctly."
        )

    return llm
