from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.embedding_provider.lower().strip()

        if self.provider != "sentence_transformers":
            raise NotImplementedError(
                f"Embedding provider '{self.settings.embedding_provider}' is not implemented yet."
            )

        self.model = _load_sentence_transformer(self.settings.embedding_model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


@lru_cache
def _load_sentence_transformer(model_name: str) -> SentenceTransformer:
    # Cached so the model loads once per API/worker process instead of every request.
    return SentenceTransformer(model_name)