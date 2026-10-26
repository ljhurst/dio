# Terraform

Shared `lj-tf-state` S3 backend. CI plans on every pull request and applies on
merge to `main` through stych's `terraform.yml`; see the root README.

`terraform.tfvars` holds only non-secret values and is committed. The
Anthropic key lives in SSM (`/dio/anthropic-api-key`) and is never in
Terraform.

## Running locally

Build the Lambda zip first; Terraform uploads it and hashes it to detect code
changes:

```bash
scripts/build_lambda.sh
AWS_PROFILE=luke-hurst-admin terraform -chdir=terraform init
AWS_PROFILE=luke-hurst-admin terraform -chdir=terraform plan
```

The build is reproducible, so an unchanged tree plans with no changes.
