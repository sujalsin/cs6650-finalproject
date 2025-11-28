output "cluster_name" {
  value = aws_ecs_cluster.cluster.name
}

output "service_name" {
  value = aws_ecs_service.svc.name
}

output "ecs_sg_id" {
  value = aws_security_group.ecs_sg.id
}
