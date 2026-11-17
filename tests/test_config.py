import pytest
from pydantic import ValidationError

from dio import config
from dio.vision.anthropic_client import AnthropicFederation

PREFIX = "DIO_ANTHROPIC_FEDERATION__"


@pytest.fixture(autouse=True)
def clear_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("RULE_ID", "ORGANIZATION_ID", "SERVICE_ACCOUNT_ID", "WORKSPACE_ID"):
        monkeypatch.delenv(PREFIX + name, raising=False)
    config.get_settings.cache_clear()


def test_federation_reads_the_lambda_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PREFIX + "RULE_ID", "fdrl_1")
    monkeypatch.setenv(PREFIX + "ORGANIZATION_ID", "org_1")
    monkeypatch.setenv(PREFIX + "SERVICE_ACCOUNT_ID", "svac_1")
    monkeypatch.setenv(PREFIX + "WORKSPACE_ID", "wrkspc_1")

    assert config.get_settings().anthropic_federation == AnthropicFederation(
        rule_id="fdrl_1",
        organization_id="org_1",
        service_account_id="svac_1",
        workspace_id="wrkspc_1",
    )


def test_federation_is_none_when_unconfigured() -> None:
    assert config.get_settings().anthropic_federation is None


def test_federation_fails_loudly_when_partially_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PREFIX + "RULE_ID", "fdrl_1")

    with pytest.raises(ValidationError):
        config.get_settings()
