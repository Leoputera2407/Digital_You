from typing import Optional

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel

from digital_twin.llm.interface import get_seleted_model_n_context_len
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()

NULL_DOC_TOKEN = "?[DOCUMENT]"
DOC_SEP_PAT = "---NEW DOCUMENT---"
QUESTION_PAT = "Query:"
ANSWER_PAT = "Answer:"
QUOTE_PAT = "Quote:"
STOP_PAT = "[STOP]"
UNCERTAIN_PAT = "?[STOP]"


class BaseChain:
    """
    Base class for generating prompts.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        prompt: Optional[PromptTemplate] = None,
    ):
        self.llm = llm
        self.prompt = prompt or self.default_prompt

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        raise NotImplementedError("This method should be overridden in subclasses.")

    def create_prompt(self, **kwargs) -> str:
        """Create a formatted prompt with the given arguments."""
        return self.prompt.format_prompt(**kwargs).to_string()

    def log_filled_prompt(self, formatted_prompt: str) -> None:
        """Log the filled prompt."""
        logger.debug(f"Filled prompt:\n{formatted_prompt}")

    def tokens_within_limit(self, formatted_prompt: str) -> bool:
        """Check if the number of tokens is within the allowed limit."""
        num_tokens_in_prompt = self.llm.get_num_tokens(formatted_prompt)
        return num_tokens_in_prompt <= get_seleted_model_n_context_len() - self.llm.dict()["max_tokens"]
