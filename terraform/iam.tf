resource "aws_iam_role" "lambda_exec" {
  name                 = "dio-lambda-exec"
  permissions_boundary = local.boundary_arn

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

locals {
  anthropic_api_key_param = "/dio/anthropic-api-key"
  boundary_arn            = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/stych/dio-boundary"
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy" "lambda_exec_ssm" {
  name = "read-anthropic-api-key"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ssm:GetParameter"
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.anthropic_api_key_param}"
      }
    ]
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
  name                 = "dio-sommething-invoke"
  permissions_boundary = local.boundary_arn

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
          "${replace(var.vercel_oidc_issuer_url, "https://", "")}:sub" = var.vercel_oidc_subjects
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
      },
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.dio.arn
        Condition = {
          Bool = {
            "lambda:InvokedViaFunctionUrl" = "true"
          }
        }
      }
    ]
  })
}
