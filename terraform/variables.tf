variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "anthropic_model" {
  description = "Anthropic model ID used for label extraction"
  type        = string
  default     = "claude-haiku-4-5"
}

variable "lambda_package_path" {
  description = "Zip built by scripts/build_lambda.sh"
  type        = string
  default     = "../dist/dio.zip"
}

# --- Vercel OIDC federation (sommething -> this Lambda) ---
# Placeholder values below are NOT real. Fill these in from Vercel's OIDC
# federation docs for the `sommething` project before `terraform apply`
# creates the Vercel-facing role — until then this module will not have
# a working invoke path from sommething. See PLAN.md open questions.

variable "vercel_oidc_issuer_url" {
  description = "Vercel's OIDC issuer URL for this project (from Vercel project settings)"
  type        = string
}

variable "vercel_oidc_thumbprint" {
  description = "TLS certificate thumbprint for the Vercel OIDC issuer (required by aws_iam_openid_connect_provider)"
  type        = string
}

variable "vercel_oidc_audience" {
  description = "Expected 'aud' claim on Vercel-issued OIDC tokens. Vercel's default (team issuer mode) is 'https://vercel.com/[TEAM_SLUG]' — 'sts.amazonaws.com' only applies if the app code passes a custom `audience` to awsCredentialsProvider."
  type        = string
}

variable "vercel_oidc_subjects" {
  description = "Vercel 'sub' claim patterns (StringLike) allowed to assume the invoke role — one per trusted environment (production/preview/development)"
  type        = list(string)
}
