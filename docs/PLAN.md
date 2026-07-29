# Dionysus (dio)

Wine label scanning service. Takes a photo of a wine label, extracts structured
data via a vision LLM, enriches a few fields with hardcoded rules, and hands
the result back to `sommething` (the wine fridge app) to save.

## Why a separate repo

`sommething` is Next.js + TS + Supabase, deployed on Vercel. This service is
Python on AWS Lambda — different runtime, different deploy target. It only
needs to talk to `sommething` over an API contract, so keeping it decoupled
avoids coupling two independent deploy lifecycles into one build/CI setup.

## Flow

1. User uploads a label photo (or photos) in `sommething`.
2. `sommething`'s Next.js backend (already has the user's Supabase session)
   calls this Lambda over HTTPS, authenticated via AWS SigV4 using temporary
   credentials obtained through Vercel OIDC federation (no static secrets).
3. Lambda sends the image to a vision LLM with a fixed JSON schema, asking it
   to extract only what's legible on the label. Fields it can't read stay
   null — no guessing.
4. Lambda applies hardcoded rules to fill in a small set of enrichment fields
   that are never on the label (see below). No search API in v1.
5. Lambda returns the structured result to `sommething`, which shows it to
   the user to confirm/edit before saving to Postgres.

## Fields and their source

### From the label (vision extraction only — never guessed/inferred)
- Producer / winery
- Wine name / cuvée
- Vintage year (or null for non-vintage)
- Country / region / appellation
- Grape variety / blend (left null if not printed — e.g. most Old World
  labels omit this; do NOT infer from region)
- ABV %
- Volume (750ml, 375ml, 1.5L, etc.)
- Wine type/color (red/white/rosé/sparkling/dessert/fortified)
- Classification tier (Grand Cru, Reserva, DOCG, etc.)
- Closure (cork/screwcap, visual)
- Certifications (organic/biodynamic/vegan, if shown)
- Barcode/UPC (if visible)

### Enrichment
- Critic score / price: Wine-Searcher API (100 free calls/day trial), scoped
  to price + aggregate critic score only — never used to override label facts
  like producer/vintage. In scope for v1 (previously deferred).
- Drinking window, vintage quality, pairings: still out of scope for v1.

### User-entered (in `sommething`, not this service's job)
- Quantity, purchase price/date/store, storage location, personal notes,
  status (in cellar/consumed).

## Value standardization

- Region/appellation: free text. A controlled list isn't practical to
  maintain across every wine region globally for v1; `sommething` can layer
  its own normalization/autocomplete later if needed.
- Country: ISO 3166-1 alpha-3 code (`FRA`, `USA`, `ITA`, ...), converted by
  the model directly from whatever's printed on the label — prompt-instructed,
  not a code-side lookup. Accuracy tracked via `evals/`; revisit with a
  deterministic lookup (e.g. `pycountry`) if the model's codes turn out
  unreliable.
- Wine type: fixed enum — `red | white | rose | sparkling | dessert |
  fortified`, or `null` if the label doesn't make it legible.
- Volume: normalize to ml, integer (750ml label → `750`, not `"750ml"`).
- Vintage: integer (4-digit year) or `null` for non-vintage/illegible — never
  the string `"NV"`.
- Grape variety: array of strings, minimally cleaned (trimmed, title-cased)
  as printed on the label. No canonical-spelling lookup table in v1 — "cab
  sauv" printed on a label stays "Cab Sauv"; only whitespace/casing is
  normalized, not the wording itself.
- Closure: fixed enum — `cork | screwcap | other`, or `null` if not visible.
- Classification: standardized to the common abbreviation where one exists
  (`DOC`, `DOCG`, `IGT`, `AOC`/`AOP`, `DO`, `DOCa`) — the model converts a
  spelled-out label (e.g. "Denominazione di Origine Controllata") to `DOC`.
  Tiers with no standard abbreviation (`Grand Cru`, `Reserva`, `Kabinett`,
  etc.) are reported as printed. Distinct from `appellation` — appellation
  is the named place, classification is the tier/system applied to it.

## Schemas (v1)

Three distinct shapes: what the vision model returns, what we get back from
Wine-Searcher (internal representation — exact vendor response TBD), and
what the Lambda hands back to `sommething`.

### 0. Request (input to Lambda)

```json
{
  "images": [
    { "data": "<base64>", "media_type": "image/jpeg" }
  ]
}
```

`images` is 1–4 entries (front label, back label, etc.) — all reasoned over
together in a single Claude request to produce one merged extraction, not
one extraction per image. `media_type` is one of the types Claude's vision
input accepts (`image/jpeg`, `image/png`, `image/webp`, `image/gif`).

### 1. Vision extraction output

Passed as `output_config.format` (`json_schema`) on the Claude call, so the
model is constrained to exactly this shape. Every field nullable except the
two array fields, which default to `[]` when nothing is legible — no
guessing, ever.

```json
{
  "type": "object",
  "properties": {
    "producer": { "type": ["string", "null"] },
    "wine_name": { "type": ["string", "null"] },
    "vintage": { "type": ["integer", "null"] },
    "country_iso_alpha_3": { "type": ["string", "null"] },
    "region": { "type": ["string", "null"] },
    "appellation": { "type": ["string", "null"] },
    "grape_varieties": { "type": "array", "items": { "type": "string" } },
    "abv_percent": { "type": ["number", "null"] },
    "volume_ml": { "type": ["integer", "null"] },
    "wine_type": {
      "anyOf": [
        { "type": "string", "enum": ["red", "white", "rose", "sparkling", "dessert", "fortified"] },
        { "type": "null" }
      ]
    },
    "classification": { "type": ["string", "null"] },
    "closure": {
      "anyOf": [
        { "type": "string", "enum": ["cork", "screwcap", "other"] },
        { "type": "null" }
      ]
    },
    "certifications": { "type": "array", "items": { "type": "string" } },
    "barcode": { "type": ["string", "null"] }
  },
  "required": [
    "producer", "wine_name", "vintage", "country_iso_alpha_3", "region",
    "appellation", "grape_varieties", "abv_percent", "volume_ml",
    "wine_type", "classification", "closure", "certifications", "barcode"
  ],
  "additionalProperties": false
}
```

`wine_type`/`closure` use `anyOf` with singular-type branches, not a
multi-type array + `enum` — the API's structured-outputs schema validator
rejects `enum` values against a `["string", "null"]` declared type (`400
Invalid schema: Enum value '...' does not match declared type`).

`country_iso_alpha_3` — the model converts whatever country name is printed
on the label to its ISO 3166-1 alpha-3 code directly (prompt-instructed, no
code-side lookup/library for now); accuracy is being validated via
`evals/`.

### 2. Wine-Searcher output (internal representation)

Not the raw vendor payload — a normalized shape our Lambda code produces
after calling Wine-Searcher, so the rest of the pipeline doesn't depend on
their wire format. Exact field mapping from the real API response is an open
question (see below); this is the target shape to map into.

```json
{
  "matched": true,
  "match_query": "Producer + wine name + vintage string sent to the API",
  "wine_searcher_url": "https://www.wine-searcher.com/find/...",
  "price": {
    "currency": "USD",
    "average": 24.99,
    "min": 19.99,
    "max": 34.99
  },
  "critic_score": {
    "score": 91,
    "scale": 100
  }
}
```

`matched: false` (with `price`/`critic_score`/`wine_searcher_url` all
`null`) when Wine-Searcher has no confident match — a miss here must never
block returning the label extraction to `sommething`.

### 3. Final Lambda response (to `sommething`)

Wraps the label extraction and enrichment separately rather than flattening
them — keeps the "never guessed" vs. "looked up" provenance visible to the
frontend, and means a Wine-Searcher failure only nulls out `enrichment`, not
the whole response.

```json
{
  "schema_version": 1,
  "label": { /* exactly the vision extraction schema above */ },
  "enrichment": {
    "matched": true,
    "wine_searcher_url": "https://www.wine-searcher.com/find/...",
    "price": { "currency": "USD", "average": 24.99, "min": 19.99, "max": 34.99 },
    "critic_score": { "score": 91, "scale": 100 }
  },
  "meta": {
    "model": "claude-haiku-4-5",
    "extracted_at": "2026-07-28T14:03:00Z",
    "warnings": []
  }
}
```

`enrichment` is `null` (not an empty object) if the Wine-Searcher call
errored or timed out — distinct from `matched: false`, which means the call
succeeded but found nothing. `meta.warnings` carries non-fatal issues (e.g.
`"wine_searcher_timeout"`) so `sommething` can surface them without the
whole request failing.

## Model choice

Anthropic, Claude Haiku 4.5 (`claude-haiku-4-5`). Small/fast tier is
sufficient — this is closer to OCR + structuring than open-ended reasoning.
$1/$5 per MTok (input/output), 200K context, vision-capable. Called via the
`anthropic` Python SDK. Downscale/compress images client-side before
sending — biggest cost lever, since vision pricing scales with image
resolution.

## Tooling & code style

- **Package/env management:** `uv` — `uv sync`, `uv run`, lockfile committed.
- **Lint/format:** `ruff` (both linting and formatting; no separate black).
- **Type checking:** `mypy`, run in CI alongside ruff.
- **Structure:** small, well-named modules — prefer more small files over
  fewer large ones. Within a module, hoist public functions to the top;
  private helpers (`_`-prefixed) go below the public functions that use
  them.
- **Functions over classes.** Reach for a plain function first; only
  introduce a class where state genuinely needs to be carried (there isn't
  an obvious case for that in this service yet — it's a single request/
  response pipeline).
- **Pydantic models, not raw dicts or long parameter lists.** The three
  schemas above (vision extraction, Wine-Searcher result, final response)
  are Pydantic models, not `TypedDict`/plain dicts — validation for free,
  and functions take one model in / return one model out rather than
  accreting positional params.
- **Comments:** none unless something is genuinely non-obvious (a vendor
  quirk, a workaround, a constraint the code can't express on its own). No
  restating what the code already says.
- **Tests:** unit tests for public functions only — private (`_`-prefixed)
  helpers are exercised indirectly through the public function that calls
  them, not tested directly. Aim for good coverage of behavior (null
  fields, enrichment miss/timeout, schema edge cases), not for hitting every
  private helper individually.

## Infra

- AWS Lambda, Python runtime.
- Lambda framework: AWS Lambda Powertools for Python (structured logging,
  tracing, Pydantic-based event/response parsing — no routing overhead
  needed for a single-endpoint function).
- Exposed via a **Lambda Function URL** with `authorization_type = "AWS_IAM"`
  (SigV4), not a public endpoint. Chose this over API Gateway: single
  endpoint, single caller, no need for routing, request validation,
  throttling tiers, or a custom domain — API Gateway's extra Terraform and
  cost aren't buying anything here. Function URLs support `AWS_IAM` auth
  natively, so IAM policy on the invoking role is the only access control
  needed. Revisit only if a second route/consumer shows up.
- Terraform: reuse patterns from `aboutme`'s AWS setup — shared S3 backend
  (`lj-tf-state` bucket, project-scoped state key), a GitHub OIDC provider
  + deploy role scoped to specific resource ARNs, and a placeholder-zip
  `aws_lambda_function` with `lifecycle { ignore_changes = [filename,
  source_code_hash] }` so Terraform doesn't fight CI deploys. New pattern
  needed here (aboutme doesn't have it): the deploy/invoke role needs
  `lambda:InvokeFunctionUrl` scoped to this one function, plus the
  Vercel OIDC trust relationship described below.
- Auth: Vercel OIDC federation → `sommething`'s Vercel deployment assumes an
  AWS IAM role via OIDC (no long-lived AWS access keys), gets temporary
  credentials, signs requests to the Lambda with SigV4.
  - Requires: AWS IAM OIDC identity provider trusting Vercel's OIDC issuer,
    an IAM role with a trust policy scoped to the `sommething` Vercel
    project, and a permission policy scoped to just `lambda:InvokeFunctionUrl`
    on this one function.
  - `sommething` never handles a static secret for this; Lambda never
    validates Supabase JWTs directly — auth trust boundary is
    Vercel-workload-identity → IAM role, not end-user identity. User auth
    stays entirely inside `sommething`.

## Implementation status

Scaffolded: `src/dio/` (models, errors, images, prompts, vision, enrichment
stub, handler), `tests/` (18 tests, all passing), `pyproject.toml`
(uv/ruff/mypy config), `terraform/` (validated with `terraform validate`,
not yet applied — needs real `anthropic_api_key` and the Vercel OIDC values
below), `.github/workflows/ci.yml` (lint/type/test on every push+PR;
build+deploy on `main`/`workflow_dispatch`, gated behind `lint-and-test`
passing).

The CI deploy job assumes an AWS role via OIDC — set the GitHub repo
variable `DIO_DEPLOY_ROLE_ARN` to the `github_actions_deploy_role_arn`
Terraform output once applied. Lambda code is deployed by CI
(`aws lambda update-function-code`), never by Terraform directly — that's
why the `aws_lambda_function` resource points at a placeholder zip with
`ignore_changes` on the hash/filename.

## Explicitly out of scope for v1
- Multiple auth methods (matches `sommething`, which is email/password only
  today).
- Barcode-lookup fallback path.

## Decisions

- **Photo count:** v1 accepts multiple photos per request (e.g. front +
  back label) — request body carries an `images` array, and the vision call
  reasons over all of them together in a single Claude request to produce
  one merged extraction.
- **Wine-Searcher:** no account/API key yet. v1 ships an `Enricher`
  interface (Protocol) with a stub implementation that always returns
  `matched: false`, so the pipeline, schemas, and Lambda handler are fully
  wired and testable now. The real Wine-Searcher client is a drop-in
  implementation of the same interface once API access exists — swapping
  it in should not touch the handler or models.

## Open questions for next session
- Prompt design for the vision call — will be drafted directly in code and
  iterated from there, not finalized in this doc first.
- Wine-Searcher API integration details: exact endpoints/fields, auth
  method, how their raw response maps onto the internal schema above,
  rate-limit/timeout handling beyond the 100/day free tier (what happens on
  429 — skip enrichment for that request, or retry?). Blocked on getting
  API access.
- Terraform: confirm reusing `lj-tf-state` (same bucket as `aboutme`, new
  state key) is fine, vs. a fully separate backend.
- Whether `sommething`'s save flow needs `schema_version` handled explicitly
  (e.g. reject/upgrade unknown versions) or can just assume `1` for now.
- Vercel OIDC issuer URL/thumbprint and the `sommething` Vercel project's
  identity — needed to write the actual trust policy condition; Terraform
  will scaffold with placeholder variables until these are supplied.
