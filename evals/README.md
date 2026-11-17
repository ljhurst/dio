# Evals

Runs `dio.vision.client.extract_label` against real photos in `cases/` and
compares the result to hand-verified `expected.json` for each case. Exact
field-by-field match for now — no fuzzy/partial-credit comparison yet.

This hits the real Anthropic API (cost, latency, non-determinism), so it's
separate from `tests/`: not part of `pytest`/CI, run manually.

## Adding a case

See `cases/README.md`.

## Running

```bash
aws sso login --profile dio-deploy
AWS_PROFILE=dio-deploy uv run python -m evals.runner
```

Sign in with `ant auth login`, or export `ANTHROPIC_API_KEY`.

Prints a PASS/FAIL line per case (with the specific fields that mismatched
on failure), then overall and per-field accuracy. Exits non-zero if any
case failed.
