# Terraform

Reuses the same patterns as `aboutme`'s AWS setup: shared `lj-tf-state` S3
backend, GitHub OIDC deploy role, placeholder-zip Lambda so Terraform
doesn't fight CI over `source_code_hash`.

## First-time setup

```bash
cp terraform.tfvars.example terraform.tfvars
# fill in terraform.tfvars — anthropic_api_key at minimum to get a plan;
# vercel_oidc_* values are required before apply actually succeeds (see
# PLAN.md open questions)

terraform init
terraform plan
```

Lambda code is deployed by CI (see `.github/workflows/ci.yml`), not by
Terraform. The `archive_file` data source in `lambda.tf` generates a
placeholder zip on every `plan`/`apply` so `terraform apply` has something
to upload on first run; `lifecycle.ignore_changes` on `filename` and
`source_code_hash` means Terraform never fights CI over the real deployed
code afterwards.

Before running against a real account, check whether the account-level
GitHub Actions OIDC provider already exists (e.g. created by `aboutme`'s
Terraform):

```bash
aws iam list-open-id-connect-providers
```

If it does, set `manage_github_oidc_provider = false` and
`github_oidc_provider_arn` to the existing ARN in `terraform.tfvars` —
creating it twice in one AWS account fails with `EntityAlreadyExists`.
