from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel
from typing import Optional, List

from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()


class BaseChain:
    """
    Base class for generating prompts.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        max_output_tokens: int,
        prompt: Optional[PromptTemplate] = None,
    ):
        self.llm = llm
        self.max_output_tokens = max_output_tokens
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
        return num_tokens_in_prompt + self.max_output_tokens <= self.llm.dict()["max_tokens"]
    
    def get_filled_prompt(self, **kwargs) -> str:
        raise NotImplementedError("This method should be overridden in subclasses.")

    @log_function_time()
    def run(self, query: str, **kwargs) -> dict:
        formatted_prompt = self.get_filled_prompt(query, **kwargs)
        return self.llm.predict(formatted_prompt)
    
    @log_function_time()
    async def async_run(self, query: str, **kwargs) -> dict:
        formatted_prompt = self.get_filled_prompt(query, **kwargs)
        return await self.llm.apredict(formatted_prompt)