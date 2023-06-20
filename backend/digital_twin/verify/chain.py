import json
from typing import Dict, List

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel
from langchain.chains.qa_generation.prompt import PROMPT_SELECTOR

from digital_twin.utils.logging import setup_logger
from digital_twin.vectordb.chunking.models import InferenceChunk

logger = setup_logger()


DOC_SEP_PAT = "---NEW DOCUMENT---"
QUESTION_PAT = "Query:"
ANSWER_PAT = "Answer:"
QUOTE_PAT = "Quote:"
STOP_PAT = "[STOP]"
UNCERTAIN_PAT = "?[STOP]"


SAMPLE_QUESTION = "How is the progress of the project?"

SAMPLE_JSON_RESPONSE = {
    "answerable": "Yes",
    "confidence score": '0.954',
}

BASE_PROMPT = (
    "Is it possible to answer the query based on provided documents?"
    "Respond with 'answerable' a binary 'Yes' or 'No' depending on whether you can answer the question or not given the provided documents.\n"
    "Respond with a 'confidence score' (between 0 and 1) depending on your confidence that you can ACCURATELY answer the question given the provided documents.\n"
)


class BaseVerify:
    """Base class for Verifing whether the question can be answered with the internal knowledge."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        context_doc: List[InferenceChunk],
        max_output_tokens: int,
        prompt: PromptTemplate = None,
    ):
        self.llm = llm
        self.context_doc = context_doc
        self.max_output_tokens = max_output_tokens
        self.prompt = prompt or self.default_prompt

    @property
    def default_prompt(self) -> PromptTemplate:
        """The default prompt."""
        return PROMPT_SELECTOR.get_prompt(self.llm)

    def predict_answer(self, formatted_prompt: str) -> str:
        """Predict an answer using the language model."""
        return self.llm.predict(formatted_prompt)

    def log_filled_prompt(self, formatted_prompt: str) -> None:
        """Log the filled prompt."""
        logger.debug(f"Filled prompt:\n{formatted_prompt}")


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
            f"Sample response:\n{json.dumps(SAMPLE_JSON_RESPONSE)}\n\n"
            f'Each context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            "Question: {question}\n"
        )
        return PromptTemplate(
            template=prompt, input_variables=["context", "question"]
        )

    def tokens_within_limit(self, formatted_prompt: str) -> bool:
        """Check if the number of tokens is within the allowed limit."""
        num_tokens_in_prompt = self.llm.get_num_tokens(formatted_prompt)
        return num_tokens_in_prompt <= self.llm.dict()["max_tokens"]

    def format_documents(self) -> str:
        """Format the documents for the prompt."""
        return "".join(
            f"{DOC_SEP_PAT}\n{ranked_document.content}\n"
            for ranked_document in self.context_doc
        ).strip()

    def create_prompt(self, question: str, **kwargs) -> str:
        """Create a formatted prompt with the given question and documents."""
        context = self.format_documents()
        return self.prompt.format_prompt(
            question=question, context=context, **kwargs
        ).to_string()

    def __call__(self, input_str: str) -> dict:
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
        return self.predict_answer(formatted_prompt)


class RefineVerify(BaseVerify):
    """Custom verify close to a refine chain."""

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        prompt = (
            "HUMAN:\n"
            f"{BASE_PROMPT}"
            "Can you answer the query based on the provided document. "
            f'Each context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            f"{QUESTION_PAT}\n{{question}}\n"
            "ASSISTANT:\n"
        )
        return PromptTemplate(
            template=prompt, input_variables=["context", "question"]
        )

    @property
    def refine_prompt(self) -> PromptTemplate:
        """Define the prompt to use for the refining step."""
        prompt = (
            "HUMAN:\n"
            "Refine the original answer to the question using the new (possibly irrelevant) document extract.\n"
            "f{BASE_PROMPT}"
            f"{QUESTION_PAT}\n---------------\n"
            "{question}\n\n"
            "Original answer:\n-----------------\n"
            "{previous_answer}\n\n"
            f'Each of the new context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            "Reminder:\n-----------------\n"
            "If the extract is not relevant or helpful, don't even talk about it. "
            "Simply copy the original answer, without adding anything.\n"
            "Do not copy the question.\n\n"
            "ASSISTANT:\n"
        )
        return PromptTemplate(
            template=prompt,
            input_variables=["context", "question", "previous_answer"],
        )

    def __call__(self, input_str: str) -> dict:
        """Ask a question."""
        last_answer = None

        for i, ranked_doc in enumerate(self.context_doc):
            print(f"Refining from document {i + 1}/{len(self.context_doc)}")
            prompt = self.default_prompt if i == 0 else self.refine_prompt
            if i == 0:
                formatted_prompt = prompt.format_prompt(
                    question=input_str, context=ranked_doc.context
                )
            else:
                formatted_prompt = prompt.format_prompt(
                    question=input_str,
                    context=ranked_doc.content,
                    previous_answer=last_answer,
                )
            last_answer = self.predict_answer(formatted_prompt)
        self.log_filled_prompt(formatted_prompt)
        return last_answer
