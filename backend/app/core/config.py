from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ragops-document-intelligence"
    app_env: str = "local"
    service_name: str = "ragops-api"

    log_level: str = "INFO"
    log_dir: str = "logs"

    file_storage_backend: str = "local"
    storage_dir: str = "storage"
    upload_dir: str = "storage/uploads"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ragops_db"
    postgres_user: str = "ragops_user"
    postgres_password: str = "ragops_password"

    redis_host: str = "localhost"
    redis_port: int = 6379

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "ragops_chunks"

    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    retrieval_top_k: int = 5

    answer_provider: str = "local_extractive"
    answer_model: str = "local_extractive_v1"
    max_context_chunks: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()