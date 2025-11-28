# S3 Bucket for image uploads
resource "aws_s3_bucket" "image_bucket" {
  bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.project}-image-processing"

  # Ignore tag changes to avoid S3 Control API issues
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# S3 Bucket Versioning (optional, but good practice)
resource "aws_s3_bucket_versioning" "image_bucket_versioning" {
  bucket = aws_s3_bucket.image_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# DynamoDB Table for processing results
resource "aws_dynamodb_table" "results_table" {
  name           = var.dynamodb_table_name != "" ? var.dynamodb_table_name : "${var.project}-image-results"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "filename"

  attribute {
    name = "filename"
    type = "S"
  }

  tags = {
    Name = "${var.project}-image-results"
  }
}

# IAM Role for Lambda (create for both local and AWS if LabRole not available)
resource "aws_iam_role" "lambda_role" {
  count = var.is_local ? 1 : (var.create_iam_role ? 1 : 0)
  
  name = "${var.project}-image-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project}-image-processor-role"
  }
}

# IAM Policy for Lambda (S3 read, DynamoDB write, CloudWatch logs)
resource "aws_iam_role_policy" "lambda_policy" {
  count = var.is_local ? 1 : (var.create_iam_role ? 1 : 0)
  
  name = "${var.project}-image-processor-policy"
  role = aws_iam_role.lambda_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.image_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.results_table.arn
      },
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

# Data source for existing LabRole (for AWS Learner Lab)
# Only use if not creating IAM role
data "aws_iam_role" "lab_role" {
  count = (var.is_local || var.create_iam_role) ? 0 : 1
  name  = "LabRole"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project}-image-processor"
  retention_in_days = 14

  tags = {
    Name = "${var.project}-image-processor-logs"
  }
}

# Lambda Function
resource "aws_lambda_function" "image_processor" {
  function_name = "${var.project}-image-processor"
  role          = var.is_local ? aws_iam_role.lambda_role[0].arn : (var.create_iam_role ? aws_iam_role.lambda_role[0].arn : data.aws_iam_role.lab_role[0].arn)
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  filename      = var.zip_file_path
  source_code_hash = filebase64sha256(var.zip_file_path)

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.results_table.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = {
    Name = "${var.project}-image-processor"
  }
}

# S3 Bucket Notification - Lambda trigger
resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = aws_s3_bucket.image_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.image_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# Lambda Permission for S3
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.image_bucket.arn
}

