from functools import lru_cache

import anthropic
import boto3
from pydantic import BaseModel

ANTHROPIC_AUDIENCE = "https://api.anthropic.com"


class AnthropicFederation(BaseModel, frozen=True):
    """The Console-side IDs a workload presents to exchange its identity token
    for an Anthropic access token. None of them are secret."""

    rule_id: str
    organization_id: str
    service_account_id: str
    workspace_id: str | None = None


@lru_cache(maxsize=1)
def get_client(federation: AnthropicFederation | None = None) -> anthropic.Anthropic:
    """With `federation`, authenticate as the Lambda's IAM role through
    Workload Identity Federation. Without it, fall back to the SDK's own
    resolution (`ANTHROPIC_API_KEY` or an `ant auth login` profile), for local
    runs such as evals."""
    if federation is None:
        return anthropic.Anthropic()

    return anthropic.Anthropic(
        credentials=anthropic.WorkloadIdentityCredentials(
            identity_token_provider=_sts_identity_token,
            federation_rule_id=federation.rule_id,
            organization_id=federation.organization_id,
            service_account_id=federation.service_account_id,
            workspace_id=federation.workspace_id,
        )
    )


def _sts_identity_token() -> str:
    # Called on every exchange: a token carrying a jti can only be exchanged once.
    response = boto3.client("sts").get_web_identity_token(
        Audience=[ANTHROPIC_AUDIENCE],
        SigningAlgorithm="RS256",
        DurationSeconds=900,
    )
    return str(response["WebIdentityToken"])
