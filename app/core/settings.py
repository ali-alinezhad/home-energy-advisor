from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.2
    llm_timeout: int = 30
    llm_max_tokens: int = 600
    mock_llm: bool = False
    log_to_file: bool = False
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
