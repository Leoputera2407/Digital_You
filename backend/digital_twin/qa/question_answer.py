import json
import re
import asyncio
from typing import (
    Dict,
    List,
    Optional,
    Any,
    Tuple,
    Union,
    AsyncIterable, 
    Awaitable,
)
from langchain import PromptTemplate
from langchain.callbacks import AsyncIteratorCallbackHandler

from digital_twin.config.constants import (
    BLURB,
    DOCUMENT_ID,
    SEMANTIC_IDENTIFIER,
    SOURCE_LINK,
    SOURCE_TYPE,
)
from digital_twin.llm.interface import get_llm
from digital_twin.llm.chains.base import (
    ANSWER_PAT,
    QUOTE_PAT,
)
from digital_twin.llm.chains.qa_chain import (
    BaseQA,
    QA_MODEL_SETTINGS,
)
from digital_twin.qa.interface import QAModel
from digital_twin.llm.chains.verify_chain import StuffVerify, VERIFY_MODEL_SETTINGS
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time
from digital_twin.utils.text_processing import (
    clean_model_quote,
    shared_precompare_cleanup,
)

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
    # if null_answer_check == UNCERTAINTY_PAT or not null_answer_check:
    #     return None, None

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
    #logger.info(f"Answer: {answer}")
    #logger.info(f"Quotes: {quote_strings}")
    if not answer or not quote_strings:
        return None, None
    quotes_dict = match_quotes_to_docs(quote_strings, chunks)
    return answer, quotes_dict

def stream_answer_end(answer_so_far: str, next_token: str) -> bool:
    next_token = next_token.replace('\\"', "")
    # If the previous character is an escape token, don't consider the first character of next_token
    if answer_so_far and answer_so_far[-1] == "\\":
        next_token = next_token[1:]
    if '"' in next_token:
        return True
    return False


def process_verify_answer(
    answer_raw: str
) -> tuple[bool | None, float | None]:
    
    def _determine_answerable(answer_str: str | None) -> bool | None:
        if answer_str is None:
            return None
        if "yes" in is_answerable.lower():
            return True
        if "no" in is_answerable.lower():
            return False
    
    def _extract_score(answer_str: str | None) -> float | None:
        if answer_str is None:
            return None
        try:
            score = re.search('(confidence|score|confidence_score|confidence_scores)\D*(\d+\.\d+)', answer_str)
            if score is not None:
                return float(score.group(2))
            else:
                return None
        except ValueError:
            return None

    try:
        model_raw_json: dict[str, str | list[str]] = json.loads(answer_raw)
        answer_dict = {k.lower(): v for k, v in model_raw_json.items()}
        is_answerable = _determine_answerable(
            str(answer_dict.get("answerable") or answer_dict.get("answer"))
        )
        confidence_score = float(
            answer_dict.get("confidence") or 
            answer_dict.get("confidence_score") or 
            answer_dict.get("confidence_scores") or 
            answer_dict.get("score")
        )
        return is_answerable, confidence_score
    except ValueError:
        is_answerable = _determine_answerable(answer_raw)
        confidence_score = _extract_score(answer_raw)
        return is_answerable, confidence_score


async def async_verify_if_docs_are_relevant(
        query: str,
        context_docs: List[InferenceChunk],
) -> tuple[bool, float]:
    verify_chain = StuffVerify(
        llm=get_llm(
            **VERIFY_MODEL_SETTINGS
        ),
    )
    res = await verify_chain.async_run(
        query,
        context_docs=context_docs
    )
    is_docs_relevant, confidence_score = process_verify_answer(res)
    # Return False if is_docs_relevant is None
    is_docs_relevant = is_docs_relevant if is_docs_relevant is not None else False
    # Return 0.0 if confidence_score is None
    confidence_score = confidence_score if confidence_score is not None else 0.0

    return is_docs_relevant, confidence_score

class QA(QAModel):
    def __init__(
        self,
        model_timeout: int,
    ) -> None:
        # Pick LLM
        self.llm = get_llm(
            **QA_MODEL_SETTINGS,
            model_timeout=model_timeout,
        )
        self.model_timeout = model_timeout

    @log_function_time()
    def answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
        add_metadata: bool = False,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        try:
            qa_system = self._pick_qa_chain(
                llm=self.llm,
                prompt=prompt,
            )
            model_output = qa_system.run(query, context_docs, add_metadata)
        except Exception as e:
            logger.exception(e)
            model_output = "Model Failure"

        logger.debug(model_output)

        answer, quotes_dict = process_answer(model_output, context_docs)
        return answer, quotes_dict
    

    @log_function_time()
    async def async_answer_question(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
        add_metadata: bool = False,
    ) -> Tuple[
        Optional[str], Dict[str, Optional[Dict[str, str | int | None]]]
    ]:
        try:
            qa_system = self._pick_qa_chain(
                llm=self.llm,
                prompt=prompt,
            )
            model_output = await qa_system.async_run(query, context_docs, add_metadata)
        except Exception as e:
            logger.exception(e)
            model_output = "Model Failure"

        logger.debug(model_output)

        answer, quotes_dict = process_answer(model_output, context_docs)
        return answer, quotes_dict
    
    @log_function_time()
    async def async_answer_question_and_verify(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
        add_metadata: bool = False,
    ) -> Tuple[
        Optional[str],
        Dict[str, Optional[Dict[str, str | int | None]]],
        Optional[bool],
        Optional[float],
    ]:
        """
        Runs both qa_response and verify chain async.
        If documents are irrelevant, returns None for answer and quotes_dict

       :return Tuple[answer, quotes_dict]
        """
        async def execute_tasks() -> List[Any]:
            tasks = {
                "qa_response": self.async_answer_question(
                    query, 
                    prompt=prompt,
                    context_docs=context_docs,
                    add_metadata=add_metadata,
                ),
                "verify_relevancy": async_verify_if_docs_are_relevant(
                    query, 
                    context_docs=context_docs
                )
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for task_name, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    raise Exception(f"Error in {task_name} coroutine: {result}")
            return results
                
        # Return the results in the order of the input tasks
        # qa_response is a tuple of (answer, quotes_dict)
        qa_response, relevancy_resp = await execute_tasks()
        answer, quotes_dict = qa_response
        is_docs_relevant, confidence_score = relevancy_resp
        
        return answer, quotes_dict, is_docs_relevant, confidence_score

    @log_function_time()
    async def answer_question_stream(
        self,
        query: str,
        context_docs: List[InferenceChunk],
        prompt: PromptTemplate = None,
    ) -> AsyncIterable[str]:
        callback = AsyncIteratorCallbackHandler()
        self.llm_streaming = get_llm(
            streaming=True,
            callback_handler=[callback],
            model_timeout=self.model_timeout,
            **QA_MODEL_SETTINGS
        )
        qa_system: BaseQA = self._pick_qa_chain(
            llm=self.llm_streaming,
            prompt=prompt,
        )

        async def wrap_done(fn: Awaitable, event: asyncio.Event):
            """Wrap an awaitable with an event to signal when it's done or an exception is raised."""
            try:
                await fn
            except Exception as e:
                print(f"Caught exception: {e}")
            finally:
                # Signal the aiter to stop.
                event.set()
                

        # Begin a task that runs in the background.
        task = asyncio.create_task(wrap_done(
            qa_system.async_run(query, context_docs),
            callback.done),
        )

        # Initialize variables
        model_output: str = ""
        found_answer_start = False
        found_answer_end = False

        # Iterate through the stream of tokens
        async for token in callback.aiter():
            # Accumulate model output
            event_text = token
            model_previous = model_output
            model_output += event_text

            # Check for answer boundaries
            if not found_answer_start and '{"answer":"' in model_output.replace(
                " ", ""
            ).replace("\n", ""):
                found_answer_start = True
                continue

            if found_answer_start and not found_answer_end:
                if stream_answer_end(model_previous, event_text):
                    found_answer_end = True
                    yield get_json_line({"answer_finished": True})
                    continue
                yield get_json_line({"answer_data": event_text})

        await task

        # Post-processing: Extract answer and quotes from the model output
        answer, quotes_dict = process_answer(model_output, context_docs)
        if answer:
            logger.info(answer)
        else:
            logger.warning(
                "Answer extraction from model output failed, most likely no quotes provided"
            )

        if quotes_dict is None:
            yield get_json_line({})
        else:
            yield get_json_line(quotes_dict)
    
