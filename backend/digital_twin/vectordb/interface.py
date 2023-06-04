import abc
from typing import Dict, List, Optional, Union

from digital_twin.connectors.model import Document
from digital_twin.vectordb.chunking.models import InferenceChunk

from digital_twin.utils.logging import setup_logger
VectorDBFilter = Dict[str, Union[str, List[str], None]]

logger = setup_logger()


class VectorDB:
    @abc.abstractmethod
    def index(self, chunks: list[Document]) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def semantic_retrieval(
        self,
        query: str,
        filters: Optional[List[VectorDBFilter]],
        num_to_retrieve: int,
    ) -> list[InferenceChunk]:
        raise NotImplementedError

