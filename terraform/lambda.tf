data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda_placeholder.zip"

  source {
    content  = "placeholder - real code deployed by CI, see .github/workflows/ci.yml"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "dio" {
  function_name = "lj-dio-extract"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "dio.handler.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      "DIO_ANTHROPIC_API_KEY" = var.anthropic_api_key
      "DIO_ANTHROPIC_MODEL"   = var.anthropic_model
    }
  }

  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_function_url" "dio" {
  function_name      = aws_lambda_function.dio.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_cloudwatch_log_group" "dio" {
  name              = "/aws/lambda/${aws_lambda_function.dio.function_name}"
  retention_in_days = 14
}
