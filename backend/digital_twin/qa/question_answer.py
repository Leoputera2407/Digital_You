import json
import re
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from sqlalchemy.orm import Session
from langchain import PromptTemplate

from digital_twin.config.constants import (
    BLURB,
    DOCUMENT_ID,
    SEMANTIC_IDENTIFIER,
    SOURCE_LINK,
    SOURCE_TYPE,
    SupportedPromptType,
)
from digital_twin.config.model_config import SupportedModelType
from digital_twin.llm import get_selected_llm_instance
from digital_twin.llm.interface import SelectedModelConfig
from digital_twin.llm.chains.qa_chain import (
    ANSWER_PAT,
    QUOTE_PAT,
    UNCERTAIN_PAT,
)
from digital_twin.qa.interface import QAModel
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.text_processing import (
    clean_model_quote,
    shared_precompare_cleanup,
)
from digital_twin.db.model import User
from digital_twin.llm.chains.qa_chain import StuffQA, RefineQA
from digital_twin.utils.timing import log_function_time
from digital_twin.indexdb.chunking.models import InferenceChunk

logger = setup_logger()


def get_json_line(json_dict: dict) -> str:
    return json.dumps(json_dict) + "\n"


def extract_answer_quotes_freeform(
    answer_raw: str,
) -> Tuple[Optional[str], Optional[list[str]]]:
    null_answer_check = (
        answer_raw.replace(ANSWER_PAT, "").replace(QUOTE_PAT, "").strip()
    )

    # If model just gives back the uncertainty pattern to signify answer isn't found or nothing at all
    if null_answer_check == UNCERTAIN_PAT or not null_answer_check:
        return None, None

    # If no answer section, don't care about the quote
    if answer_raw.lower().strip().startswith(QUOTE_PAT.lower()):
        return None, None

    # Sometimes model regenerates the Answer: pattern despite it being provided in the prompt
    if answer_raw.lower().startswith(ANSWER_PAT.lower()):
        answer_raw = answer_raw[len(ANSWER_PAT) :]

    # Accept quote sections starting with the lower case version
    answer_raw = answer_raw.replace(
        f"\n{QUOTE_PAT}".lower(), f"\n{QUOTE_PAT}"
    )  # Just in case model unreliable

    sections = re.split(rf"(?<=\n){QUOTE_PAT}", answer_raw)
    sections_clean = [
        str(section).strip() for section in sections if str(section).strip()
    ]
    if not sections_clean:
        return None, None

    answer = str(sections_clean[0])
    if len(sections) == 1:
        return answer, None
    return answer, sections_clean[1:]


def extract_answer_quotes_json(
    answer_dict: dict[str, str | list[str]]
) -> Tuple[Optional[str], Optional[list[str]]]:
    answer_dict = {k.lower(): v for k, v in answer_dict.items()}
    answer = str(answer_dict.get("answer"))
    quotes = answer_dict.get("quotes") or answer_dict.get("quote")
    if isinstance(quotes, str):
        quotes = [quotes]
    return answer, quotes


def separate_answer_quotes(
    answer_raw: str,
) -> Tuple[Optional[str], Optional[list[str]]]:
    try:
        model_raw_json = json.loads(answer_raw)
        return extract_answer_quotes_json(model_raw_json)
    except ValueError:
        return extract_answer_quotes_freeform(answer_raw)


def match_quotes_to_docs(
    quotes: list[str],
    chunks: list[InferenceChunk],
    prefix_only_length: int = 100,
) -> Dict[str, Dict[str, Union[str, int, None]]]:
    quotes_dict: dict[str, dict[str, Union[str, int, None]]] = {}
    for quote in quotes:
        for chunk in chunks:
            if not chunk.source_links:
                continue

            quote_clean = shared_precompare_cleanup(
                clean_model_quote(quote, trim_length=prefix_only_length)
            )
            chunk_clean = shared_precompare_cleanup(chunk.content)

            if quote_clean not in chunk_clean:
                continue
            offset = chunk_clean.index(quote_clean)

            # Extracting the link from the offset
            curr_link = None
            for link_offset, link in chunk.source_links.items():
                # Should always find one because offset is at least 0 and there must be a 0 link_offset
                if int(link_offset) <= offset:
                    curr_link = link
                else:
                    quotes_dict[quote] = {
                        DOCUMENT_ID: chunk.document_id,
                        SOURCE_LINK: curr_link,
                        SOURCE_TYPE: chunk.source_type,
                        SEMANTIC_IDENTIFIER: chunk.semantic_identifier,
                        BLURB: chunk.blurb,
                    }
                    break
            quotes_dict[quote] = {
                DOCUMENT_ID: chunk.document_id,
                SOURCE_LINK: curr_link,
                SOURCE_TYPE: chunk.source_type,
                SEMANTIC_IDENTIFIER: chunk.semantic_identifier,
                BLURB: chunk.blurb,
            }
            break
    return quotes_dict


def process_answer(
    answer_raw: str, chunks: list[InferenceChunk]
) -> tuple[str | None, dict[str, dict[str, str | int | None]] | None]:
    answer, quote_strings = separate_answer_quotes(answer_raw)
    if not answer or not quote_strings:
        return None, None
    quotes_dict = match_quotes_to_docs(quote_strings, chunks)
    return answer, quotes_dict

class QA(QAModel):
    def __init__(
        self,
        db_session: Session,
        model_config: SelectedModelConfig,
        max_output_tokens: int = SupportedModelType.GPT3_5.n_context_len,
        user: Optional[User] = None,
    ) -> None:
        # Pick LLM
        self.llm = get_selected_llm_instance(
            user, 
            db_session,
            model_config, 
            max_output_tokens=max_output_tokens
        )
        self.max_output_tokens = max_output_tokens

    @log_function_time()
    def answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt_type: SupportedPromptType = SupportedPromptType.STUFF,
        prompt: PromptTemplate = None,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        try:
            qa_system: Union[StuffQA,RefineQA] = self._pick_qa(
                prompt_type=prompt_type,
                llm=self.llm,
                context_doc=context_docs,
                max_output_tokens=self.max_output_tokens,
                prompt=prompt,
            )
            model_output = qa_system.run(query)
        except Exception as e:
            logger.exception(e)
            model_output = "Model Failure"

        logger.debug(model_output)

        answer, quotes_dict = process_answer(model_output, context_docs)
        return answer, quotes_dict
    

    @log_function_time()
    def async_answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt_type: SupportedPromptType = SupportedPromptType.STUFF,
        prompt: PromptTemplate = None,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        try:
            qa_system: Union[StuffQA,RefineQA] = self._pick_qa(
                prompt_type=prompt_type,
                llm=self.llm,
                context_doc=context_docs,
                max_output_tokens=self.max_output_tokens,
                prompt=prompt,
            )
            model_output = qa_system.async_run(query)
        except Exception as e:
            logger.exception(e)
            model_output = "Model Failure"

        logger.debug(model_output)

        answer, quotes_dict = process_answer(model_output, context_docs)
        return answer, quotes_dict

    def answer_question_stream(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt_type: SupportedPromptType =  SupportedPromptType.STUFF,
        prompt: PromptTemplate = None,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        try:
            qa_system: Union[StuffQA,RefineQA] = self._pick_qa(
                prompt_type=prompt_type,
                llm=self.llm,
                context_doc=context_docs,
                max_output_tokens=self.max_output_tokens,
                prompt=prompt,
            )
            yield qa_system(query)
        except Exception as e:
            logger.exception(e)
            model_output = "Model Failure"

        logger.debug(model_output)

        answer, quotes_dict = process_answer(model_output, context_docs)
        yield quotes_dict
