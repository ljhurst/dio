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

- `DIO_ANTHROPIC_API_KEY` (required)
- `DIO_ANTHROPIC_MODEL` (default `claude-haiku-4-5`)
