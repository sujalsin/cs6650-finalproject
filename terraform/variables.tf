variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "project" {
  type    = string
  default = "order-processing-part2"
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "task_cpu" {
  type    = number
  default = 256
}

variable "task_memory" {
  type    = number
  default = 512
}

variable "min_tasks" {
  type    = number
  default = 2
}

variable "max_tasks" {
  type    = number
  default = 4
}

variable "cpu_target_percent" {
  type    = number
  default = 70
}

variable "scale_in_cooldown_seconds" {
  type    = number
  default = 300
}

variable "scale_out_cooldown_seconds" {
  type    = number
  default = 300
}

# Lambda configuration variables
variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda function"
  type        = number
  default     = 10
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

# Toggle variables for Part 3
variable "enable_lambda_processor" {
  description = "Enable Lambda-based order processor"
  type        = bool
  default     = true
}

variable "enable_ecs_processor" {
  description = "Enable ECS-based order processor"
  type        = bool
  default     = false
}

# LocalStack configuration
variable "is_local" {
  description = "Whether deploying to LocalStack (true) or AWS (false)"
  type        = bool
  default     = false
}

# Image processing Lambda configuration
variable "image_processor_s3_bucket_name" {
  description = "Name of the S3 bucket for image processing (optional, will be auto-generated if not provided)"
  type        = string
  default     = ""
}

variable "image_processor_dynamodb_table_name" {
  description = "Name of the DynamoDB table for image processing results (optional, will be auto-generated if not provided)"
  type        = string
  default     = ""
}

variable "image_processor_lambda_zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
  default     = "function.zip"
}

variable "create_iam_role" {
  description = "Whether Terraform should create the Lambda IAM role"
  type        = bool
  default     = false
}
