resource "aws_secretsmanager_secret" "app" {
  name = "${var.project_name}-${var.environment}-app-secrets"
  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DATABASE_URL      = "postgresql+psycopg://${var.db_username}:${random_password.db.result}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
    ANTHROPIC_API_KEY = var.anthropic_api_key
    JWT_SECRET_KEY    = var.jwt_secret_key
  })
}
