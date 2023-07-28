from digital_twin.config.constants import DocumentSource
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.connectors.factory import identify_connector_class
from digital_twin.utils.logging import setup_logger

logger = setup_logger()

def add_metadata_section(
    chunk: InferenceChunk,
) -> str:
    prompt = ""
    prompt += f"DOCUMENT SOURCE: {chunk.source_type}\n"
    if chunk.metadata:
        prompt += f"METADATA:\n"
        connector_class = identify_connector_class(DocumentSource(chunk.source_type))
        for metadata_line in connector_class.parse_metadata(chunk.metadata):
            prompt += f"\t{metadata_line}\n"
        prompt += '\n\n'
    return prompt