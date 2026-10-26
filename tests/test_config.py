import pytest
from aws_lambda_powertools.utilities import parameters

from dio import config


@pytest.fixture(autouse=True)
def clear_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DIO_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DIO_ANTHROPIC_API_KEY_PARAM", raising=False)
    config.get_settings.cache_clear()
    config.get_anthropic_api_key.cache_clear()


def test_api_key_from_environment_skips_ssm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIO_ANTHROPIC_API_KEY", "env-key")

    def fail(*args: object, **kwargs: object) -> str:
        raise AssertionError("SSM must not be read when the key is in the environment")

    monkeypatch.setattr(parameters, "get_parameter", fail)

    assert config.get_anthropic_api_key() == "env-key"


def test_api_key_read_from_ssm_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, bool]] = []

    def get_parameter(name: str, decrypt: bool = False) -> str:
        calls.append((name, decrypt))
        return "ssm-key"

    monkeypatch.setattr(parameters, "get_parameter", get_parameter)

    assert config.get_anthropic_api_key() == "ssm-key"
    assert config.get_anthropic_api_key() == "ssm-key"
    assert calls == [("/dio/anthropic-api-key", True)]


def test_api_key_param_name_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIO_ANTHROPIC_API_KEY_PARAM", "/dio/other")
    names: list[str] = []

    def get_parameter(name: str, decrypt: bool = False) -> str:
        names.append(name)
        return "k"

    monkeypatch.setattr(parameters, "get_parameter", get_parameter)

    config.get_anthropic_api_key()

    assert names == ["/dio/other"]
