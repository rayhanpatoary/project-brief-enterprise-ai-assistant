from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    openai_api_key: SecretStr = SecretStr('')
    openai_chat_model: str = 'gpt-4o-mini'
    openai_embedding_model: str = 'text-embedding-3-small'
    chroma_persist_directory: Path = Path('data/chroma')
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_document_chars: int = Field(default=2_000_000, gt=0)
    chunk_size: int = Field(default=1000, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)
    retrieval_k: int = Field(default=5, ge=1, le=20)

    def require_key(self) -> str:
        key = self.openai_api_key.get_secret_value()
        if not key.strip():
            raise ConfigurationError('Set OPENAI_API_KEY in your environment or .env file.')
        return key


class ConfigurationError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    pass


@lru_cache
def get_settings() -> Settings:
    return Settings()
