import abc
from collections.abc import AsyncIterable
from typing import Dict, List, Optional, Tuple, Union

from langchain import PromptTemplate
from langchain.llms.base import BaseLanguageModel

from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.llm.chains.qa_chain import BaseQA, StuffQA
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


class QAModel:
    def _pick_qa_chain(
        self,
        llm: BaseLanguageModel,
        prompt: PromptTemplate = None,
    ) -> BaseQA:
        return StuffQA(
            llm=llm,
            prompt=prompt,
        )

    @abc.abstractmethod
    def answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
    ) -> Tuple[Optional[str], Optional[Dict[str, Dict[str, Union[str, int, None]]]]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def async_answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
    ) -> Tuple[Optional[str], Optional[Dict[str, Dict[str, Union[str, int, None]]]]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def async_answer_question_and_verify(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
    ) -> Tuple[
        Optional[str],
        Optional[Dict[str, Optional[Dict[str, str | int | None]]]],
        Optional[bool],
        Optional[float],
    ]:
        raise NotImplementedError

    @abc.abstractmethod
    def answer_question_stream(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
    ) -> AsyncIterable[str]:
        raise NotImplementedError
