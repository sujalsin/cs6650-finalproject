variable "project" {
  description = "Project name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "zip_file_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to monitor"
  type        = string
  default     = ""
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for results"
  type        = string
  default     = ""
}

variable "is_local" {
  description = "Whether deploying to LocalStack"
  type        = bool
  default     = false
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 30
}

variable "create_iam_role" {
  description = "Whether to create IAM role (true) or use existing LabRole (false)"
  type        = bool
  default     = true
}

