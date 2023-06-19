from enum import Enum

from digital_twin.vectordb.chunking.models import EmbeddedIndexChunk, IndexChunk

class Embedder:
    def embed(self, chunks: list[IndexChunk]) -> list[EmbeddedIndexChunk]:
        raise NotImplementedError