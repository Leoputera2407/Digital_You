import json
from typing import Dict, List

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel
from langchain.chains.qa_generation.prompt import PROMPT_SELECTOR

from digital_twin.utils.logging import setup_logger
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.llm.chains.base import BaseChain

logger = setup_logger()


DOC_SEP_PAT = "---NEW DOCUMENT---"
QUESTION_PAT = "Query:"
ANSWER_PAT = "Answer:"
QUOTE_PAT = "Quote:"
STOP_PAT = "[STOP]"
UNCERTAIN_PAT = "?[STOP]"


SAMPLE_JSON_RESPONSE = {
    "answerable": "Yes",
    "confidence score": '0.954',
}

BASE_PROMPT = (
    "Is it possible to answer the query based on provided documents?"
    "Respond with 'answerable' a binary 'Yes' or 'No' depending on whether you can answer the question or not given the provided documents.\n"
    "Respond with a 'confidence score' (between 0 and 1) depending on your confidence that you can ACCURATELY answer the question given the provided documents.\n"
)


class BaseVerify(BaseChain):
    """Base class for Verifing whether the question can be answered with the internal knowledge."""

    def __init__(
            self, 
            llm: BaseLanguageModel, 
            context_doc: List[InferenceChunk], 
            max_output_tokens: int, 
            prompt: PromptTemplate = None
        ) -> None:
        super().__init__(llm, max_output_tokens, prompt)  
        self.context_doc = context_doc

    def run(self, input_str: str) -> dict:
        formatted_prompt = self.get_filled_prompt(input_str)
        return self.llm.predict(formatted_prompt)
    
    async def async_run(self, input_str: str) -> dict:
        formatted_prompt = self.get_filled_prompt(input_str)
        return await self.llm.apredict(formatted_prompt)


class StuffVerify(BaseVerify):
    """
    Custom verify close to a stuff chain.
    Compared to the default stuff chain which may exceed the context size,
    this chain loads as many documents as allowed by the context size.
    Since it uses all the context size, it's meant for a "one-shot" question,
    not leaving space for a follow-up question which exactly contains the previous one.
    """

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        prompt = (
            "HUMAN:\n"
            f"{BASE_PROMPT}"
            f"Please answer in this format:\n{json.dumps(SAMPLE_JSON_RESPONSE)}\n\n"
            f'Each context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            "Question: {question}\n"
        )
        return PromptTemplate(
            template=prompt, input_variables=["context", "question"]
        )

   
    def format_documents(self) -> str:
        """Format the documents for the prompt."""
        return "".join(
            f"{DOC_SEP_PAT}\n{ranked_document.content}\n"
            for ranked_document in self.context_doc
        ).strip()

    def create_prompt(self, question: str) -> str:
        """Create a formatted prompt with the given question and documents."""
        context = self.format_documents()
        return self.prompt.format_prompt(
            question=question, context=context
        ).to_string()

    def get_filled_prompt(self, input_str: str) -> str:
        documents = []

        for ranked_doc in self.context_doc:
            documents.append(ranked_doc)
            formatted_prompt = self.create_prompt(input_str, documents)
            if not self.tokens_within_limit(formatted_prompt):
                documents.pop()
                break

        print(f"Stuffed {len(documents)} documents in the context")
        formatted_prompt = self.create_prompt(input_str, documents)
        self.log_filled_prompt(formatted_prompt)
        return formatted_prompt
    
