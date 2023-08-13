import json
from typing import Dict, List, Optional

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel

from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.llm.chains.base import DOC_SEP_PAT, QUESTION_PAT, BaseChain
from digital_twin.llm.chains.utils import add_metadata_section
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()

SAMPLE_QUESTION = "Where is the Eiffel Tower?"
SAMPLE_DOCUMENT = (
    "The Eiffel Tower is an iconic symbol of Paris, France. It is located on the Champ de Mars in France."
)

SAMPLE_JSON_RESPONSE = {
    "answerable": "Yes",
    "confidence_score": "0.954",
}

SAMPLE_JSON_CANNOT_ANSWER = {
    "answerable": "No",
    "confidence_score": "0.0",
}


BASE_PROMPT = (
    "Is it possible to answer the query based on provided documents?"
    "Respond with 'answerable' a binary 'Yes' or 'No' depending on whether you can answer the question or not given the provided documents.\n"
    "Respond with a 'confidence score' (between 0 and 1) depending on your confidence that you can ACCURATELY answer the question given the provided documents.\n"
    f"Sample question and response:\n"
    f"{QUESTION_PAT}\n{SAMPLE_QUESTION}\n"
    f"{DOC_SEP_PAT}\n{SAMPLE_DOCUMENT}\n"
    f"{json.dumps(SAMPLE_JSON_RESPONSE).replace('{', '{{').replace('}', '}}')}\n\n"
    "If you are unsure of the answer or if it isn't provided in the extracts, "
    f"respond with {json.dumps(SAMPLE_JSON_CANNOT_ANSWER).replace('{', '{{').replace('}', '}}')}.\n"
)
VERIFY_MODEL_SETTINGS = {"temperature": 0.0, "max_output_tokens": 100}


class BaseVerify(BaseChain):
    """Base class for Verifing whether the question can be answered with the internal knowledge."""

    def __init__(self, llm: BaseLanguageModel, prompt: PromptTemplate = None) -> None:
        super().__init__(llm, prompt)

    def get_filled_prompt(self, query: str, context_docs: Optional[List[InferenceChunk]]) -> str:
        raise NotImplementedError("Implement in subclass")

    @log_function_time()
    def run(self, query: str, context_docs: Optional[List[InferenceChunk]]) -> str:
        formatted_prompt = self.get_filled_prompt(query, context_docs)
        return self.llm.predict(formatted_prompt)

    @log_function_time()
    async def async_run(self, query: str, context_docs: Optional[List[InferenceChunk]]) -> str:
        formatted_prompt = self.get_filled_prompt(query, context_docs)
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
            "---START OF INSTRUCTIONS---\n"
            f"{BASE_PROMPT}"
            "---END OF INSTRUCTIONS---\n"
            f'Each context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            "Question: {question}\n"
        )
        return PromptTemplate(template=prompt, input_variables=["context", "question"])

    def format_documents(self, documents: List[InferenceChunk]) -> str:
        """Format the documents for the prompt."""
        formatted_docs = ""
        for ranked_document in documents:
            formatted_docs += f"{DOC_SEP_PAT}\n"
            formatted_docs += add_metadata_section(ranked_document)
            formatted_docs += f"{ranked_document.content}\n"
        return formatted_docs.strip()

    def get_filled_prompt(self, query: str, context_doc: Optional[List[InferenceChunk]]) -> str:
        documents = []
        if context_doc:
            for ranked_doc in context_doc:
                documents.append(ranked_doc)
                formatted_prompt = self.create_prompt(question=query, context=documents)
                if not self.tokens_within_limit(formatted_prompt):
                    documents.pop()
                    break

        print(f"Stuffed {len(documents)} documents in the context")
        formatted_prompt = self.create_prompt(question=query, context=documents)
        self.log_filled_prompt(formatted_prompt)
        return formatted_prompt
