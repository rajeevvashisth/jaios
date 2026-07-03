output "alb_dns_name" {
  description = "Point your domain's CNAME/ALIAS here (or use it directly over HTTP for a first smoke test)."
  value       = aws_lb.this.dns_name
}

output "backend_ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "secrets_manager_secret_arn" {
  value = aws_secretsmanager_secret.app.arn
}
