import json
from uuid import UUID
from nltk.corpus import stopwords  # type:ignore
from nltk.stem import WordNetLemmatizer  # type:ignore
from nltk.tokenize import word_tokenize  # type:ignore


from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.config.app_config import NUM_RETURNED_HITS
from digital_twin.indexdb.interface import IndexFilter, KeywordIndex
from digital_twin.utils.logging import setup_logger
from digital_twin.utils.timing import log_function_time

logger = setup_logger()


def lemmatize_text(text: str) -> list[str]:
    lemmatizer = WordNetLemmatizer()
    word_tokens = word_tokenize(text)
    return [lemmatizer.lemmatize(word) for word in word_tokens]


def remove_stop_words(text: str) -> list[str]:
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    return [word for word in word_tokens if word.casefold() not in stop_words]


def keyword_search_query_processing(query: str) -> str:
    query = " ".join(remove_stop_words(query))
    query = " ".join(lemmatize_text(query))
    return query



