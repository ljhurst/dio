from functools import lru_cache

from aws_lambda_powertools.utilities import parameters
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIO_")

    anthropic_api_key: str | None = None
    anthropic_api_key_param: str = "/dio/anthropic-api-key"
    anthropic_model: str = "claude-haiku-4-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_anthropic_api_key() -> str:
    settings = get_settings()
    if settings.anthropic_api_key:
        return settings.anthropic_api_key
    return str(parameters.get_parameter(settings.anthropic_api_key_param, decrypt=True))
