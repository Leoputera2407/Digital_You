import json
from typing import List, Optional

from langchain import PromptTemplate
from langchain.base_language import BaseLanguageModel

from digital_twin.llm.chains.base import (
    BaseChain,
    QUESTION_PAT,
    DOC_SEP_PAT,
    UNCERTAIN_PAT,
)
from digital_twin.llm.chains.utils import add_metadata_section
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time


logger = setup_logger()


SAMPLE_QUESTION = "Where is the Eiffel Tower?"

SAMPLE_JSON_RESPONSE = {
    "answer": "The Eiffel Tower is located in Paris, France.",
    "quotes": [
        "The Eiffel Tower is an iconic symbol of Paris",
        "located on the Champ de Mars in France.",
    ],
}

SAMPLE_JSON_CANNOT_ANSWER = {
    "answer": UNCERTAIN_PAT,
    "quotes": [],
}

BASE_PROMPT = (
    f"Answer the query based on provided documents and quote relevant sections. "
    f"If you are unsure of the answer or if it isn't provided in the extracts, "
    f"respond with {json.dumps(SAMPLE_JSON_CANNOT_ANSWER).replace('{', '{{').replace('}', '}}')}.\n"
    f"Respond with a json containing answering the user's query and quote the most relevant quotes from the documents provided."
    f"The quotes must be EXACT substrings from the documents.\n"
    f"Sample question and response:\n"
    f"{QUESTION_PAT}\n{SAMPLE_QUESTION}\n"
    f"{json.dumps(SAMPLE_JSON_RESPONSE).replace('{', '{{').replace('}', '}}')}\n\n"
)

QA_MODEL_SETTINGS = {"temperature": 0.0, "max_output_tokens": 2000}
class BaseQA(BaseChain):
    """Base class for Question-Answering."""

    def __init__(
            self, 
            llm: BaseLanguageModel, 
            prompt: PromptTemplate = None
        ) -> None:
        super().__init__(llm, prompt)  
    
    @log_function_time()
    def run(self, 
            input_str: str, 
            context_docs: Optional[List[InferenceChunk]],
            add_metadata: bool = False
        ) ->str :
        formatted_prompt = self.get_filled_prompt(input_str, context_docs, add_metadata)
        return self.llm.predict(formatted_prompt)
    
    @log_function_time()
    async def async_run(
        self, 
        input_str: str, 
        context_docs: Optional[List[InferenceChunk]],
        add_metadata: bool = False
    ) -> str:
        formatted_prompt = self.get_filled_prompt(input_str, context_docs, add_metadata)
        return await self.llm.apredict(formatted_prompt)
    

class StuffQA(BaseQA):
    """
    Custom QA close to a stuff chain.
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
            f'Each context document below is prefixed with "{DOC_SEP_PAT}".\n\n'
            "{context}\n\n---\n\n"
            f"{QUESTION_PAT}\n{{question}}\n"
        )
        return PromptTemplate(
            template=prompt, input_variables=["context", "question"]
        )

    def format_documents(self, documents: List[InferenceChunk], add_metadata:bool = False) -> str:
        """Format the documents for the prompt."""
        return "".join(
            f"{DOC_SEP_PAT}\n{ranked_document.content}\n"
            for ranked_document in documents
        ).strip()
    
    # def format_documents(self, documents: List[InferenceChunk], add_metadata: bool = False) -> str:
    #     """Format the documents for the prompt."""
    #     formatted_docs = ""
    #     for ranked_document in documents:
    #         formatted_docs += f"{DOC_SEP_PAT}\n"
    #         if add_metadata:
    #             formatted_docs = add_metadata_section(formatted_docs, ranked_document)
    #         formatted_docs += f"{ranked_document.content}\n"
    #     return formatted_docs.strip()
    

    def create_prompt(self, question: str, documents: List[InferenceChunk], add_metadata: bool = False) -> str:
        """Create a formatted prompt with the given question and documents."""
        context = self.format_documents(documents, add_metadata=add_metadata)
        return self.prompt.format_prompt(
            question=question, context=context
        ).to_string()
    
    def get_filled_prompt(
            self, 
            input_str: str, 
            context_docs: Optional[List[InferenceChunk]],
            add_metadata: bool = False
        ) -> str:
        documents = []
        if context_docs:
            for ranked_doc in context_docs:
                documents.append(ranked_doc)
                formatted_prompt = self.create_prompt(input_str, documents, add_metadata)
                if not self.tokens_within_limit(formatted_prompt):
                    documents.pop()
                    break

        logger.info(f"Stuffed {len(documents)} documents in the context")
        formatted_prompt = self.create_prompt(input_str, documents)
        self.log_filled_prompt(formatted_prompt)
        return formatted_prompt


class RefineQA(BaseQA):
    """Custom QA close to a refine chain."""

    @property
    def default_prompt(self) -> PromptTemplate:
        """Define the default prompt."""
        prompt = (
            "HUMAN:\n"
            f"{BASE_PROMPT}"
            "Answer the query based on the provided document. "
            "If you are unsure of the answer or if it isn't provided in the document, "
            "answer 'Unknown[STOP]'. Conclude your answer with '[STOP]' when you're finished. "
            "Avoid adding any extraneous information.\n\n"
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
    
    def get_filled_prompt(self) -> str:
       raise NotImplementedError("RefineQA does not support get_filled_prompt")

    @log_function_time()
    def run(self, input_str: str, context_doc: List[InferenceChunk]) -> dict:
        """Ask a question."""
        last_answer = None

        for i, ranked_doc in enumerate(context_doc):
            print(f"Refining from document {i + 1}/{len(context_doc)}")
            prompt = self.default_prompt if i == 0 else self.refine_prompt
            if i == 0:
                formatted_prompt = prompt.format_prompt(
                    question=input_str, context=ranked_doc.content
                )
            else:
                formatted_prompt = prompt.format_prompt(
                    question=input_str,
                    context=ranked_doc.content,
                    previous_answer=last_answer,
                )
            last_answer = self.llm.predict(formatted_prompt)
        self.log_filled_prompt(formatted_prompt)
        return last_answer
    
    async def run(self) -> dict:
        """Ask a question."""
        raise NotImplementedError("RefineQA is not yet implemented for async")
