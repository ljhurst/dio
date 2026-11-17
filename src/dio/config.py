from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from dio.vision.anthropic_client import AnthropicFederation


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIO_", env_nested_delimiter="__")

    anthropic_model: str = "claude-haiku-4-5"
    anthropic_federation: AnthropicFederation | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
