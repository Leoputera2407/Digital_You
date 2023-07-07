from digital_twin.config.constants import DocumentSource
from digital_twin.indexdb.chunking.models import InferenceChunk
from digital_twin.connectors.factory import identify_connector_class
from digital_twin.llm.chains.base import METADATA_END_PAT


def add_metadata_section(
    prompt_current: str,
    chunk: InferenceChunk,
    prepend_tab: bool = True,
) -> str:
    def _prepend(s: str, ppt: bool) -> str:
        return "\t" + s if ppt else s

    prompt_current += _prepend(f"DOCUMENT SOURCE: {chunk.source_type}\n", prepend_tab)
    if chunk.metadata:
        prompt_current += _prepend(f"METADATA:\n", prepend_tab)
        connector_class = identify_connector_class(DocumentSource(chunk.source_type))
        for metadata_line in connector_class.parse_metadata(chunk.metadata):
            prompt_current += _prepend(f"\t{metadata_line}\n", prepend_tab)
        prompt_current += METADATA_END_PAT + '\n\n'
    return prompt_current