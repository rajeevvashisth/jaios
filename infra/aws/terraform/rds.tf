resource "random_password" "db" {
  length  = 24
  special = false # avoid characters that need escaping in a connection-string URL
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}"
  subnet_ids = module.vpc.private_subnets
  tags       = local.tags
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Postgres from the backend ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

# pgvector ships with RDS Postgres 15.3+ / 16.x — `CREATE EXTENSION IF NOT
# EXISTS vector` already runs as part of Alembic migration 0001, so no
# custom parameter group is needed to enable it.
resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-${var.environment}"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage_gb
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period   = 7
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final"
  deletion_protection       = var.environment == "production"

  tags = local.tags
}
