from digital_twin.indexdb.chunking.models import EmbeddedIndexChunk, IndexChunk


class Embedder:
    def embed(self, chunks: list[IndexChunk]) -> list[EmbeddedIndexChunk]:
        raise NotImplementedError
