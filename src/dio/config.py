from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIO_")

    anthropic_api_key: str
    anthropic_model: str = "claude-haiku-4-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
