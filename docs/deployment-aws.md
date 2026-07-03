# Deploying JAIOS to AWS

This is a **skeleton**, not a one-click production deploy: it stands up a
real, working architecture (VPC, RDS Postgres+pgvector, ECR, ECS Fargate,
an ALB routing `/api/*` to the backend and everything else to the
frontend) that matches Phase 1's promise — "AWS deployment later is a
matter of swapping the Postgres connection string and containerizing the
same images" — but a few things (HTTPS, autoscaling, WAF, multi-AZ NAT) are
left as documented TODOs rather than guessed defaults for infrastructure
this repo has never actually been deployed to.

## Prerequisites

- An AWS account and credentials configured for the CLI/Terraform (`aws
  configure` or equivalent env vars).
- Terraform >= 1.6, Docker, the AWS CLI.
- A domain, if you want HTTPS — the skeleton ships HTTP-only on the ALB
  (see the TODO in `infra/aws/terraform/alb.tf`).

## 1. Provision infrastructure

```bash
cd infra/aws/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars — at minimum set jwt_secret_key (openssl rand -hex 32)

terraform init
terraform plan
terraform apply
```

This creates the VPC, RDS instance, ECR repositories, ECS cluster, IAM
roles, the ALB, and empty ECS services (no task will run successfully yet
— there's no image in ECR to pull). Note the outputs:
`backend_ecr_repository_url`, `frontend_ecr_repository_url`,
`alb_dns_name`.

## 2. Build and push images

```bash
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

docker build -f infra/docker/backend.prod.Dockerfile -t <backend-ecr-url>:latest .
docker push <backend-ecr-url>:latest

# NEXT_PUBLIC_API_BASE_URL is baked in at build time (see the Dockerfile's
# comment) — this must be the ALB's public URL, not localhost.
docker build -f infra/docker/frontend.prod.Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://<alb_dns_name> \
  -t <frontend-ecr-url>:latest .
docker push <frontend-ecr-url>:latest
```

## 3. Roll out the services

```bash
aws ecs update-service --cluster jaios-production --service jaios-backend --force-new-deployment
aws ecs update-service --cluster jaios-production --service jaios-frontend --force-new-deployment
```

The backend container runs `alembic upgrade head` on start, same as local
Docker Compose — no separate migration step.

## 4. First-run checklist

- Hit `http://<alb_dns_name>/health` — `checks.database` should read `ok`.
- Hit `http://<alb_dns_name>/` — the dashboard should load (empty, no
  company yet).
- Register the first user via the UI's `/login` page (or `POST
  /api/auth/register`) — becomes that company's admin.
- Set `ANTHROPIC_API_KEY` (or the OpenAI/Ollama equivalent) in the
  Secrets Manager secret (`secrets_manager_secret_arn` output) before
  starting any workflow that calls an LLM.

## Known gaps in this skeleton (fix before real production traffic)

- **No HTTPS.** Add an ACM certificate + 443 listener + 80→443 redirect;
  the TODO is marked in `alb.tf`.
- **No autoscaling.** `backend_desired_count`/`frontend_desired_count` are
  fixed; add `aws_appautoscaling_target`/`_policy` if load varies.
- **Single NAT gateway.** Cheap but a single point of failure for private
  subnet egress; switch to one per AZ for real HA (see the comment in
  `vpc.tf`).
- **No WAF / rate limiting** in front of the ALB.
- **DockerTool/GitHubTool are unavailable in this container.** The
  production backend image has no `docker` or `gh` CLI (see
  `backend.prod.Dockerfile`'s comment) — Docker-in-Docker isn't available
  on Fargate without privileged mode anyway. If DevOps/Developer agents
  need real Docker or `gh` access in this deployment, that has to be a
  separate execution environment the tool shells out to remotely, not this
  container.
- **Base images drift.** Rebuild and re-push images periodically even with
  no code changes, to pick up upstream OS security patches in the
  `node:22-alpine`/`python:3.12-slim` base layers.
- **Terraform state is local by default.** Uncomment the `backend "s3"`
  block in `main.tf` before more than one person/machine ever runs
  `apply` against this.
