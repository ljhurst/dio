resource "aws_iam_role" "lambda_exec" {
  name = "lj-dio-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_exec_logs" {
  name = "lambda-cloudwatch-logs"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# --- GitHub Actions OIDC (CI deploy) ---
#
# The GitHub Actions OIDC provider (url = token.actions.githubusercontent.com)
# is an AWS-account-level resource — only one can exist per account per URL.
# If `aboutme`'s Terraform has already created it in this account, creating
# it again here will fail with EntityAlreadyExists. Check first
# (`aws iam list-open-id-connect-providers`) and set
# `manage_github_oidc_provider = false` + `github_oidc_provider_arn` to the
# existing one if so.

resource "aws_iam_openid_connect_provider" "github_actions" {
  count = var.manage_github_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

locals {
  github_oidc_provider_arn = (
    var.manage_github_oidc_provider
    ? aws_iam_openid_connect_provider.github_actions[0].arn
    : var.github_oidc_provider_arn
  )

  github_actions_oidc_condition = {
    StringEquals = {
      "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
    }
    StringLike = {
      "token.actions.githubusercontent.com:sub" = [
        "repo:${var.github_repo}:ref:refs/heads/${var.github_actions_deploy_branch}",
        "repo:${var.github_repo}@*:ref:refs/heads/${var.github_actions_deploy_branch}",
      ]
    }
  }
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "lj-dio-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["sts:AssumeRoleWithWebIdentity", "sts:TagSession"]
      Principal = {
        Federated = local.github_oidc_provider_arn
      }
      Condition = local.github_actions_oidc_condition
    }]
  })
}

resource "aws_iam_role_policy" "github_actions_deploy_lambda" {
  name = "deploy-lambda-code"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction"
        ]
        Resource = aws_lambda_function.dio.arn
      }
    ]
  })
}

# --- Vercel OIDC (sommething -> this Lambda's Function URL) ---
#
# Placeholder issuer/audience/subject values live in variables.tf and must
# be filled in from Vercel's OIDC federation docs for the `sommething`
# project before this is usable. sommething never gets a static AWS key —
# it exchanges a Vercel-issued OIDC token for temporary credentials via
# this role, then SigV4-signs the Function URL request.

resource "aws_iam_openid_connect_provider" "vercel" {
  url             = var.vercel_oidc_issuer_url
  client_id_list  = [var.vercel_oidc_audience]
  thumbprint_list = [var.vercel_oidc_thumbprint]
}

resource "aws_iam_role" "sommething_invoke" {
  name = "lj-dio-sommething-invoke"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = aws_iam_openid_connect_provider.vercel.arn
      }
      Condition = {
        StringEquals = {
          "${replace(var.vercel_oidc_issuer_url, "https://", "")}:aud" = var.vercel_oidc_audience
        }
        StringLike = {
          "${replace(var.vercel_oidc_issuer_url, "https://", "")}:sub" = var.vercel_oidc_subject
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "sommething_invoke_function_url" {
  name = "invoke-dio-function-url"
  role = aws_iam_role.sommething_invoke.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunctionUrl"
        Resource = aws_lambda_function.dio.arn
        Condition = {
          StringEquals = {
            "lambda:FunctionUrlAuthType" = "AWS_IAM"
          }
        }
      }
    ]
  })
}
