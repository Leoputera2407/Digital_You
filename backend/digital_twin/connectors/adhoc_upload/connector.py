from pathlib import Path
from typing import Any

from digital_twin.config.app_config import INDEX_BATCH_SIZE
from digital_twin.connectors.adhoc_upload.utils import check_file_ext_is_valid, get_file_ext, process_file
from digital_twin.connectors.interfaces import GenerateDocumentsOutput, LoadConnector
from digital_twin.connectors.model import Document
from digital_twin.utils.logging import setup_logger

logger = setup_logger()


class AdhocUploadConnector(LoadConnector):
    def __init__(
        self,
        file_locations: list[Path | str],
        batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.file_locations = [Path(file_location) for file_location in file_locations]
        self.batch_size = batch_size

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        pass

    def load_from_state(self) -> GenerateDocumentsOutput:
        documents: list[Document] = []

        for file_location in self.file_locations:
            if not check_file_ext_is_valid(get_file_ext(str(file_location))):
                logger.warning(f"Skipping file '{file_location}' with invalid extension")
                continue

            documents_generator = process_file(str(file_location))
            for document in documents_generator:
                documents.append(document)
                if len(documents) >= self.batch_size:
                    yield documents
                    documents = []

        if documents:
            yield documents
