variable "project" {
  type = string
}

variable "aws_region" {
  type = string
}

# Networking
variable "vpc_id" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

# ALB
variable "alb_sg_id" {
  type        = string
  default     = ""
  description = "ALB security group ID (optional for background services)"
}

variable "target_group_arn" {
  type        = string
  default     = ""
  description = "Target group ARN (optional for background services)"
}

# Container
variable "container_image" {
  type = string
}

variable "container_port" {
  type = number
}

# Task sizing
variable "task_cpu" {
  type = number
}

variable "task_memory" {
  type = number
}

# Scaling
variable "min_tasks" {
  type = number
}

variable "max_tasks" {
  type = number
}

variable "cpu_target_percent" {
  type = number
}

variable "scale_in_cooldown_seconds" {
  type = number
}

variable "scale_out_cooldown_seconds" {
  type = number
}

# Logs
variable "log_group_name" {
  type = string
}

# IAM toggles and optional pre-existing role ARNs
variable "create_iam" {
  type    = bool
  default = true
}

variable "execution_role_arn" {
  description = "If set, use this role for ECS execution; when null and create_iam=true, the module creates one."
  type        = string
  default     = null
}

variable "task_role_arn" {
  description = "If set, use this role for the ECS task; when null and create_iam=true, the module creates one."
  type        = string
  default     = null
}

variable "environment_variables" {
  description = "Environment variables to pass to the container"
  type        = map(string)
  default     = {}
}
