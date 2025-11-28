output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "receiver_service_name" {
  value = module.ecs_receiver.service_name
}

output "processor_service_name" {
  value = module.ecs_processor.service_name
}

output "cluster_name" {
  value = module.ecs_receiver.cluster_name
}

output "receiver_ecr_repository_url" {
  value = module.ecr_receiver.repository_url
}

output "processor_ecr_repository_url" {
  value = module.ecr_processor.repository_url
}

output "sns_topic_arn" {
  value = module.messaging.sns_topic_arn
}

output "sqs_queue_url" {
  value = module.messaging.sqs_queue_url
}

# Lambda outputs
output "lambda_function_arn" {
  value = module.lambda_processor.lambda_function_arn
}

output "lambda_function_name" {
  value = module.lambda_processor.lambda_function_name
}

output "lambda_log_group_name" {
  value = module.lambda_processor.lambda_log_group_name
}

output "lambda_dlq_url" {
  value = module.lambda_processor.dlq_url
}

output "lambda_ecr_repository_url" {
  value = module.ecr_lambda.repository_url
}

# Image Processing Lambda outputs
output "image_processor_lambda_function_arn" {
  value = module.image_processor.lambda_function_arn
}

output "image_processor_lambda_function_name" {
  value = module.image_processor.lambda_function_name
}

output "image_processor_s3_bucket_name" {
  value = module.image_processor.s3_bucket_name
}

output "image_processor_s3_bucket_arn" {
  value = module.image_processor.s3_bucket_arn
}

output "image_processor_dynamodb_table_name" {
  value = module.image_processor.dynamodb_table_name
}

output "image_processor_dynamodb_table_arn" {
  value = module.image_processor.dynamodb_table_arn
}
