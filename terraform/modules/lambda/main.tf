# Lambda function
resource "aws_lambda_function" "order_processor" {
  function_name = "${var.project}-order-processor"
  role          = data.aws_iam_role.lab_role.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  
  memory_size = var.memory_size
  timeout     = var.timeout
  
  # reserved_concurrency_limit = var.reserved_concurrency
  
  environment {
    variables = var.environment_variables
  }
  
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }
  
  tracing_config {
    mode = "Active"
  }
  
  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
  ]
  
  tags = {
    Name = "${var.project}-order-processor"
  }
}

# Reserved concurrency will be set manually after deployment
# resource "aws_lambda_concurrency_config" "order_processor" {
#   function_name = aws_lambda_function.order_processor.function_name
#   reserved_concurrency_limit = var.reserved_concurrency
# }


# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project}-order-processor"
  retention_in_days = 14
  
  tags = {
    Name = "${var.project}-lambda-logs"
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name = "${var.project}-order-processor-dlq"
  
  message_retention_seconds = 1209600 # 14 days
  
  tags = {
    Name = "${var.project}-order-processor-dlq"
  }
}

# Data source for existing LabRole
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# SNS Topic Subscription
resource "aws_sns_topic_subscription" "lambda_subscription" {
  topic_arn = var.sns_topic_arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.order_processor.arn
}

# Lambda Permission for SNS
resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.order_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.sns_topic_arn
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "lambda_dashboard" {
  dashboard_name = "${var.project}-lambda-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.order_processor.function_name],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", aws_lambda_function.order_processor.function_name],
            [".", "ReservedConcurrency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Concurrency"
          period  = 300
        }
      }
    ]
  })
}
