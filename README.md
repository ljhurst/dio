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

- `DIO_ANTHROPIC_API_KEY_PARAM`: SSM SecureString holding the Anthropic key
  (default `/dio/anthropic-api-key`); the Lambda reads it at cold start
- `DIO_ANTHROPIC_API_KEY`: the key itself, for local runs such as the evals;
  when set, SSM is not read
- `DIO_ANTHROPIC_MODEL` (default `claude-haiku-4-5`)

## Deployment

Merging to `main` deploys through
[stych](https://github.com/ljhurst/stych)'s shared workflows:

- **Pull request**: builds the Lambda zip and comments the Terraform plan.
- **Merge to `main`**: applies the plan, which uploads the new code.

GitHub Actions authenticates to AWS with OIDC (no stored AWS secrets) and
applies only from the `prod` environment, which is limited to `main`. The
Anthropic key is written to SSM outside Terraform:

```bash
aws ssm put-parameter --name /dio/anthropic-api-key --type SecureString --overwrite --value ...
```
