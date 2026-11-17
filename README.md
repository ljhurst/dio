# dio

Wine label scanning service for `sommething`. See `PLAN.md` for the full
design (flow, schemas, infra decisions).

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

## Environment

The Lambda reads config via `dio.config.Settings` (env vars, prefix `DIO_`):

- `DIO_ANTHROPIC_FEDERATION__RULE_ID`, `__ORGANIZATION_ID`,
  `__SERVICE_ACCOUNT_ID`, `__WORKSPACE_ID`: the Claude Console IDs for workload
  identity federation. When none are set, the SDK falls back to
  `ANTHROPIC_API_KEY` or an `ant auth login` profile, which is how the evals
  run locally. Setting only some fails at startup.
- `DIO_ANTHROPIC_MODEL` (default `claude-haiku-4-5`)

## Deployment

Merging to `main` deploys through
[stych](https://github.com/ljhurst/stych)'s shared workflows:

- **Pull request**: builds the Lambda zip and comments the Terraform plan.
- **Merge to `main`**: applies the plan, which uploads the new code.

GitHub Actions authenticates to AWS with OIDC (no stored AWS secrets) and
applies only from the `prod` environment, which is limited to `main`. The
Lambda calls the Anthropic API without a key, through Workload Identity
Federation: its role mints an AWS-signed token with `sts:GetWebIdentityToken`
and exchanges it for a short-lived Anthropic token. Setting it up once:

1. stych enables outbound identity federation for the account and allows
   `dio-lambda-exec` in the dio boundary.
2. In the Claude Console, Settings > Workload identity > Connect workload > AWS:
   register stych's issuer, create a service account, and a rule matching
   `arn:aws:iam::<account>:role/dio-lambda-exec` with audience
   `https://api.anthropic.com`.
3. Put the rule, organization, service account and workspace IDs in
   `anthropic_federation` in `terraform/terraform.tfvars`.

Denied exchanges show their reason on the Console's Workload identity history tab.
