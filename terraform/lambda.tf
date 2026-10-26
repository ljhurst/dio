resource "aws_lambda_function" "dio" {
  function_name = "lj-dio-extract"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "dio.handler.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      "DIO_ANTHROPIC_API_KEY_PARAM" = local.anthropic_api_key_param
      "DIO_ANTHROPIC_MODEL"         = var.anthropic_model
    }
  }

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)
}

resource "aws_lambda_function_url" "dio" {
  function_name      = aws_lambda_function.dio.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_cloudwatch_log_group" "dio" {
  name              = "/aws/lambda/${aws_lambda_function.dio.function_name}"
  retention_in_days = 14
}
