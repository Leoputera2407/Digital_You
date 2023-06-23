from typing import Optional

from langchain.llms.base import BaseLanguageModel
from sqlalchemy.orm.session import Session

from digital_twin.llm.config import get_api_key
from digital_twin.llm.interface import SelectedModelConfig
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


from digital_twin.db.model import User

def get_selected_llm_instance(
    db_session: Session,
    model_config: SelectedModelConfig,
    user: Optional[User] = None,
    **kwargs
) -> Optional[BaseLanguageModel]:
    llm: BaseLanguageModel = None
    api_key = get_api_key(
        db_session,
        user,
        model_config.platform,
    )
    if not api_key:
        raise ValueError("API key wasn't set for {model_config.platform}}")
   
    if model_config.name.startswith("gpt"):
        from langchain.chat_models import ChatOpenAI
        llm = ChatOpenAI(
            model_name=model_config.name,
            api_key=api_key,
            temperature=model_config.temperature,
            max_tokens=kwargs.get(
                "max_output_tokens", 500
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
                "max_output_tokens", 500
            ),
            streaming=False,
        )

    else:
        raise ValueError(
            "Only OpenAI or Claude is supported right now. Make sure you set up your .env correctly."
        )

    return llm
