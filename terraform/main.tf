terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.0.2"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # LocalStack endpoint overrides
  dynamic "endpoints" {
    for_each = var.is_local ? [1] : []
    content {
      s3       = "http://localhost:4566"
      lambda   = "http://localhost:4566"
      dynamodb = "http://localhost:4566"
      sts      = "http://localhost:4566"
      iam      = "http://localhost:4566"
      logs     = "http://localhost:4566"
    }
  }

  # LocalStack-specific settings
  skip_credentials_validation = var.is_local
  skip_metadata_api_check     = var.is_local
  skip_region_validation      = var.is_local
}

data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# LabRole should already have SNS/SQS permissions

# -----------------------------
# 1) Networking (VPC, subnets)
# -----------------------------
module "network" {
  source = "./modules/network"

  project              = var.project
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
}

# -----------------------------
# 2) CloudWatch Logs
# -----------------------------
module "logging" {
  source     = "./modules/logging"
  project    = var.project
  aws_region = var.aws_region
}

# -----------------------------
# 3) Messaging (SNS/SQS)
# -----------------------------
module "messaging" {
  source  = "./modules/messaging"
  project = var.project
}

# -----------------------------
# 4) ECR repositories
# -----------------------------
module "ecr_receiver" {
  source  = "./modules/ecr"
  project = "${var.project}-receiver"
}

module "ecr_processor" {
  source  = "./modules/ecr"
  project = "${var.project}-processor"
}

module "ecr_lambda" {
  source  = "./modules/ecr"
  project = "${var.project}-lambda"
}

# -----------------------------
# 5) ALB, TG, Listener
# -----------------------------
module "alb" {
  source         = "./modules/alb"
  project        = var.project
  vpc_id         = module.network.vpc_id
  public_subnets = module.network.public_subnet_ids
  container_port = var.container_port
}

# ---------------------------------------------------
# Docker provider + Build and Push image to ECR
# ---------------------------------------------------

# Get ECR credentials for Docker provider
data "aws_ecr_authorization_token" "ecr" {}

# Configure Docker provider to push to ECR
provider "docker" {
  registry_auth {
    # strip scheme for some docker provider versions
    address  = replace(data.aws_ecr_authorization_token.ecr.proxy_endpoint, "https://", "")
    username = data.aws_ecr_authorization_token.ecr.user_name
    password = data.aws_ecr_authorization_token.ecr.password
  }
}

# Build Order Receiver image
resource "docker_image" "order_receiver" {
  name = "${module.ecr_receiver.repository_url}:latest"

  build {
    context  = "../src/order-receiver"
    platform = "linux/amd64"
  }

  keep_locally = false
  depends_on   = [module.ecr_receiver]
}

# Push Order Receiver image to ECR
resource "docker_registry_image" "order_receiver" {
  name       = docker_image.order_receiver.name
  depends_on = [module.ecr_receiver]
}

# Build Order Processor image
resource "docker_image" "order_processor" {
  name = "${module.ecr_processor.repository_url}:latest"

  build {
    context  = "../src/order-processor"
    platform = "linux/amd64"
  }

  keep_locally = false
  depends_on   = [module.ecr_processor]
}

# Push Order Processor image to ECR
resource "docker_registry_image" "order_processor" {
  name       = docker_image.order_processor.name
  depends_on = [module.ecr_processor]
}

# Build Lambda Order Processor image
resource "docker_image" "order_processor_lambda" {
  name = "${module.ecr_lambda.repository_url}:latest"

  build {
    context  = "../src/order-processor-lambda"
    platform = "linux/amd64"
  }

  keep_locally = false
  depends_on   = [module.ecr_lambda]
}

# Push Lambda Order Processor image to ECR
resource "docker_registry_image" "order_processor_lambda" {
  name       = docker_image.order_processor_lambda.name
  depends_on = [module.ecr_lambda]
}

# -----------------------------
# 6) ECS Services
# -----------------------------

# Order Receiver Service (handles HTTP requests)
module "ecs_receiver" {
  source = "./modules/ecs"

  project    = "${var.project}-receiver"
  aws_region = var.aws_region

  # Networking
  vpc_id          = module.network.vpc_id
  private_subnets = module.network.private_subnet_ids

  # ALB wiring
  alb_sg_id        = module.alb.alb_sg_id
  target_group_arn = module.alb.target_group_arn

  # Container image
  container_image = docker_registry_image.order_receiver.name
  container_port  = var.container_port

  # Task sizing
  task_cpu    = var.task_cpu
  task_memory = var.task_memory

  # Service scaling (fixed at 1 task for receiver)
  min_tasks = 1
  max_tasks = 1

  cpu_target_percent         = var.cpu_target_percent
  scale_in_cooldown_seconds  = var.scale_in_cooldown_seconds
  scale_out_cooldown_seconds = var.scale_out_cooldown_seconds

  # Logging
  log_group_name = module.logging.log_group_name

  create_iam         = false
  execution_role_arn = data.aws_iam_role.lab_role.arn
  task_role_arn      = data.aws_iam_role.lab_role.arn

  # Environment variables for Order Receiver
  environment_variables = {
    SNS_TOPIC_ARN = module.messaging.sns_topic_arn
  }
}

# Order Processor Service (background worker)
module "ecs_processor" {
  source = "./modules/ecs"

  project    = "${var.project}-processor"
  aws_region = var.aws_region

  # Networking
  vpc_id          = module.network.vpc_id
  private_subnets = module.network.private_subnet_ids

  # No ALB for processor (it's a background service)
  # alb_sg_id and target_group_arn will use default empty values

  # Container image
  container_image = docker_registry_image.order_processor.name
  container_port  = var.container_port

  # Task sizing
  task_cpu    = var.task_cpu
  task_memory = var.task_memory

  # Service scaling (fixed at 1 task for processor)
  min_tasks = 1
  max_tasks = 1

  cpu_target_percent         = var.cpu_target_percent
  scale_in_cooldown_seconds  = var.scale_in_cooldown_seconds
  scale_out_cooldown_seconds = var.scale_out_cooldown_seconds

  # Logging
  log_group_name = module.logging.log_group_name

  create_iam         = false
  execution_role_arn = data.aws_iam_role.lab_role.arn
  task_role_arn      = data.aws_iam_role.lab_role.arn

  # Environment variables for Order Processor
          environment_variables = {
            SQS_QUEUE_URL = module.messaging.sqs_queue_url
            WORKER_COUNT  = "10"
          }
}

# -----------------------------
# 7) Lambda Order Processor
# -----------------------------
module "lambda_processor" {
  source = "./modules/lambda"

  project    = var.project
  aws_region = var.aws_region

  # Container image
  image_uri = docker_registry_image.order_processor_lambda.name

  # SNS configuration
  sns_topic_arn = module.messaging.sns_topic_arn

  # Lambda configuration
  reserved_concurrency = var.lambda_reserved_concurrency
  memory_size          = var.lambda_memory_size
  timeout              = var.lambda_timeout

  # Environment variables
  environment_variables = {
    # DLQ_URL will be set after Lambda is created
  }
}

# -----------------------------
# 8) Image Processing Lambda (S3-triggered)
# -----------------------------
module "image_processor" {
  source = "./modules/image-processor"

  project    = var.project
  aws_region = var.aws_region
  is_local   = var.is_local

  # Lambda deployment package
  zip_file_path = var.image_processor_lambda_zip_path

  # Resource names (optional, will be auto-generated if not provided)
  s3_bucket_name      = var.image_processor_s3_bucket_name
  dynamodb_table_name = var.image_processor_dynamodb_table_name

  # Lambda configuration
  lambda_memory_size = var.lambda_memory_size
  lambda_timeout     = var.lambda_timeout

  # IAM role creation toggle
  create_iam_role = var.create_iam_role
}
