-- Runs automatically on first Postgres container init (mounted into
-- /docker-entrypoint-initdb.d). Alembic migration 0001 also creates this
-- extension defensively, so a non-Docker Postgres works too.
CREATE EXTENSION IF NOT EXISTS vector;
