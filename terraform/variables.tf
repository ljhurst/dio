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

variable "anthropic_api_key" {
  description = "Anthropic API key for the vision extraction call"
  type        = string
  sensitive   = true
}

variable "anthropic_model" {
  description = "Anthropic model ID used for label extraction"
  type        = string
  default     = "claude-haiku-4-5"
}

variable "github_repo" {
  description = "GitHub repo (owner/name) allowed to assume the CI deploy role via OIDC"
  type        = string
  default     = "ljhurst/dio"
}

variable "github_actions_deploy_branch" {
  description = "Branch ref allowed to assume the CI deploy role (deploys only run from this branch)"
  type        = string
  default     = "main"
}

variable "manage_github_oidc_provider" {
  description = "Whether this state creates the account-level GitHub Actions OIDC provider. Set false (and provide github_oidc_provider_arn) if another project's Terraform (e.g. aboutme) already created it — only one can exist per AWS account."
  type        = bool
  default     = false
}

variable "github_oidc_provider_arn" {
  description = "ARN of an existing GitHub Actions OIDC provider, used when manage_github_oidc_provider is false"
  type        = string
  default     = ""
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
  description = "Expected 'aud' claim on Vercel-issued OIDC tokens"
  type        = string
  default     = "sts.amazonaws.com"
}

variable "vercel_oidc_subject" {
  description = "Expected 'sub' claim identifying the sommething Vercel project/environment (exact format from Vercel docs)"
  type        = string
}
