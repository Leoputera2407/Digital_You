from typing import Optional, Tuple

from langchain.llms.base import BaseLanguageModel
from langchain.callbacks import AsyncIteratorCallbackHandler

from digital_twin.config.app_config import DEFAULT_MODEL_TYPE
from digital_twin.config.app_config import MODEL_API_KEY
from digital_twin.config.model_config import SupportedModelType
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def get_selected_model_type() -> SupportedModelType:
    return SupportedModelType[DEFAULT_MODEL_TYPE]

def get_seleted_model_n_context_len() -> int:
    return get_selected_model_type().n_context_len


def get_llm(
    temperature: float,
    max_output_tokens: Optional[int] = None,
    streaming: bool = False,
    callback_handler: Optional[AsyncIteratorCallbackHandler] = None,
    **kwargs,
) -> Optional[BaseLanguageModel]:
    selected_model_type = get_selected_model_type()
    llm: BaseLanguageModel = None
    api_key = MODEL_API_KEY
    if not api_key:
        raise ValueError("API key wasn't set for {selected_model_type.platform}}")
    if streaming and not callback_handler:
        raise ValueError("Need to pass callback_handler for streaming")
 
    if selected_model_type.name.startswith("gpt"):
        from langchain.chat_models import ChatOpenAI
        llm = ChatOpenAI(
            model_name=selected_model_type.name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_output_tokens,
            streaming=streaming,
            callbacks=callback_handler,
            request_timeout=kwargs.get("model_timeout", 10),
        )

    elif selected_model_type.name.startswith("claude"):
        from langchain.chat_models import ChatAnthropic

        llm = ChatAnthropic(
            model=selected_model_type.name,
            antrhopic_api_key=api_key,
            temperature=temperature,
            max_tokens=max_output_tokens,
            streaming=streaming,
            callbacks=callback_handler,
            request_timeout=kwargs.get("model_timeout", 10),
        )
    elif selected_model_type.name.startswith("azure"):
         from langchain.chat_models import AzureChatOpenAI
         llm = AzureChatOpenAI(
                openai_api_base="https://prosona.openai.azure.com/",
                openai_api_version="2023-03-15-preview",
                deployment_name='35turbo',
                model="gpt-35-turbo",
                openai_api_key=api_key,
                openai_api_type='azure',
                temperature=temperature,
                max_tokens=max_output_tokens,
                streaming=streaming,
                callbacks=callback_handler,
                request_timeout=kwargs.get("model_timeout", 10),
                # We want to use the same encoding as GPT3.5, somehow this error out
                # we put `gpt-35-turbo` eventho the mapping is there.
                tiktoken_model_name="gpt-3.5-turbo"
            )

    else:
        raise ValueError(
            "Only OpenAI, Claude, and Azure is supported right now. Make sure you set up your .env correctly."
        )

    return llm