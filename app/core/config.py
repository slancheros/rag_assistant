from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ai_provider: Literal["openai", "ollama"] = "ollama"

    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = "https://api.openai.com/v1"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_api_key: SecretStr = SecretStr("ollama")

    llm_model: str = "qwen3:4b"
    embedding_model: str = "embeddinggemma"

    knowledge_base_path: Path = Path("knowledge_base.md")

    relevance_threshold: float = Field(
        default=0.35,
        ge=-1.0,
        le=1.0,
    )

    top_k: int = Field(
        default=2,
        ge=1,
        le=10,
    )

    provider_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
    )

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()