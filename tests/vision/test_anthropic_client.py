from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from dio.vision import anthropic_client
from dio.vision.anthropic_client import AnthropicFederation

FEDERATION = AnthropicFederation(
    rule_id="fdrl_1",
    organization_id="org_1",
    service_account_id="svac_1",
    workspace_id="wrkspc_1",
)


@pytest.fixture(autouse=True)
def fresh_client_cache() -> Iterator[None]:
    anthropic_client.get_client.cache_clear()
    yield
    anthropic_client.get_client.cache_clear()


def test_get_client_with_federation_exchanges_an_sts_token() -> None:
    with (
        patch("anthropic.WorkloadIdentityCredentials") as credentials,
        patch("anthropic.Anthropic") as client_class,
    ):
        anthropic_client.get_client(FEDERATION)

    credentials.assert_called_once_with(
        identity_token_provider=anthropic_client._sts_identity_token,
        federation_rule_id="fdrl_1",
        organization_id="org_1",
        service_account_id="svac_1",
        workspace_id="wrkspc_1",
    )
    client_class.assert_called_once_with(credentials=credentials.return_value)


def test_get_client_reuses_one_client_so_warm_lambdas_keep_their_token() -> None:
    with patch("anthropic.Anthropic"):
        first = anthropic_client.get_client(FEDERATION)
        second = anthropic_client.get_client(FEDERATION)

    assert first is second


def test_get_client_without_federation_uses_the_sdk_default_credentials() -> None:
    with patch("anthropic.Anthropic") as client_class:
        anthropic_client.get_client()

    client_class.assert_called_once_with()


def test_sts_identity_token_requests_an_anthropic_audience_jwt() -> None:
    sts = MagicMock()
    sts.get_web_identity_token.return_value = {"WebIdentityToken": "jwt"}

    with patch("boto3.client", return_value=sts) as boto:
        token = anthropic_client._sts_identity_token()

    assert token == "jwt"
    boto.assert_called_once_with("sts")
    sts.get_web_identity_token.assert_called_once_with(
        Audience=["https://api.anthropic.com"],
        SigningAlgorithm="RS256",
        DurationSeconds=900,
    )
