output "function_url" {
  description = "Lambda Function URL (IAM-authenticated) that sommething invokes"
  value       = aws_lambda_function_url.dio.function_url
}

output "function_arn" {
  description = "ARN of the dio Lambda function"
  value       = aws_lambda_function.dio.arn
}

output "github_actions_deploy_role_arn" {
  description = "Role ARN for GitHub Actions to assume when deploying Lambda code"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "sommething_invoke_role_arn" {
  description = "Role ARN sommething's Vercel deployment assumes via OIDC to invoke the Function URL"
  value       = aws_iam_role.sommething_invoke.arn
}
