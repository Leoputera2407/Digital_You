import abc
from collections.abc import Generator
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain import PromptTemplate
from langchain.llms.base import BaseLanguageModel

from digital_twin.config.constants import SupportedPromptType
from digital_twin.verify.chain import RefineVerify, StuffVerify
from digital_twin.utils.logging import setup_logger
from digital_twin.vectordb.chunking.models import InferenceChunk

logger = setup_logger()


class VerifyModel:
    def _pick_verify(
        prompt_type: SupportedPromptType,
        llm: BaseLanguageModel,
        context_doc: List[InferenceChunk],
        max_output_tokens: int,
        prompt: PromptTemplate = None,
    ):
        if prompt_type is prompt_type.STUFF:
            return StuffVerify(
                llm=llm,
                context_doc=context_doc,
                max_output_tokens=max_output_tokens,
                prompt=prompt,
            )
        elif prompt_type is prompt_type.REFINE:
            return RefineVerify(
                llm=llm,
                context_doc=context_doc,
                max_output_tokens=max_output_tokens,
                prompt=prompt,
            )
        else:
            logger.debug("Unsupported prompt type {prompt_type.value} passed")
            raise ("Unsupportedprompt type {prompt_type.value} passed")

    @abc.abstractmethod
    def answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt_type: SupportedPromptType,
        prompt: PromptTemplate = None,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        raise NotImplementedError

    @abc.abstractmethod
    def answer_question_stream(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt_type: SupportedPromptType,
        prompt: PromptTemplate = None,
    ) -> Generator[Optional[Dict[str, Any]], None, None]:
        raise NotImplementedError
