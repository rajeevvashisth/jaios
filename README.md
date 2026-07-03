# JAIOS — Jyka AI Operating System

A company-wide agentic operating system for Jyka Labs: 8 core agents (CEO,
CTO, Developer, DevOps, QA, Finance, Legal, Operations) orchestrated with
LangGraph, backed by a company/product/project/task domain model, a
Postgres+pgvector memory and knowledge layer, a governed tool framework, a
Next.js dashboard, JWT auth, and Prometheus metrics — deployable locally via
Docker Compose or to AWS via the included Terraform skeleton.

See [`docs/architecture.md`](docs/architecture.md) for the full architecture
across all five phases (domain model, agent registry, orchestration design,
database schema, frontend structure, observability, auth, cloud readiness).

## Prerequisites

- Docker + Docker Compose (recommended path), **or** Python 3.12+ and
  Node 20+ for running backend/frontend natively against a local Postgres.
- At least one LLM provider credential (`ANTHROPIC_API_KEY` or
  `OPENAI_API_KEY`) — or run fully local via Ollama (`DEFAULT_LLM_PROVIDER=ollama`).
- Optional, for the Developer/DevOps agents' tool integrations: the
  [`claude`](https://claude.com/claude-code) CLI (or `openhands`, via
  `CODING_WORKER_BACKEND=openhands`) on PATH for the Developer agent's
  coding worker, and the [`gh`](https://cli.github.com/) CLI (authenticated)
  for PR/issue tools. Both degrade to a clear "not available" result rather
  than failing the workflow when missing.

## Run with Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY or OPENAI_API_KEY, or switch to ollama

docker compose up --build
```

- Backend API: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432

The backend container runs `alembic upgrade head` on startup, so the schema
(including the `vector` extension) is created automatically.

Ports collide often if you run more than one Next.js/Postgres project
locally — override any of `FRONTEND_PORT` / `BACKEND_PORT` / `POSTGRES_PORT`
in `.env` (docker-compose.yml already parameterizes all three) rather than
stopping the other project.

**If you already have Ollama running natively** (`brew install ollama` /
ollama.ai, `ollama serve`), don't bother with the `local-models` profile —
point the backend at your existing install instead, which gets you Metal
GPU acceleration instead of the CPU-only VM Docker runs in:

```bash
# in .env:
OLLAMA_BASE_URL=http://host.docker.internal:11434
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2:latest   # or whatever `ollama list` shows you have
```

`host.docker.internal` is the container's route back to the host machine —
`localhost` inside the backend container refers to the container itself,
not your Mac, which is the most common way this setting goes wrong.

Otherwise, to run a bundled local model server instead:

```bash
docker compose --profile local-models up --build
# then, in another shell:
docker compose exec ollama ollama pull llama3.2
# and in .env: OLLAMA_BASE_URL=http://ollama:11434 (the compose service name)
```

## Run natively (no Docker)

Backend:

```bash
cd backend
python3.12 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
cp ../.env.example ../.env   # edit DATABASE_URL to point at your local Postgres
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## First steps once it's running

1. Open http://localhost:3000/settings and create a company (this is the
   top-level entity everything else hangs off).
2. Add a product or two on the Products page (or via `POST /api/products`).
3. Go to Workflows and start a `task_delegation` or `portfolio_review` run
   with a goal — watch it move through the agent chain, and approve the
   DevOps deploy checkpoint when it pauses.
4. Check Logs for the full audit trail of what each agent and tool call did.
5. Add a few entries on the Finance page and an obligation or two on the
   Compliance page — the Overview dashboard, the product detail pages, and
   the "ask the agent" buttons on Finance/Compliance all key off this data.
6. Register an account at http://localhost:3000/login (the first user for
   a company becomes its admin) — approving/rejecting a workflow's human
   checkpoint now requires being signed in.
7. Check http://localhost:8000/metrics for Prometheus-format metrics and
   http://localhost:8000/health for a DB-aware health check.

## Development

```bash
make test        # pytest (DB-backed tests skip if Postgres isn't reachable)
make lint         # ruff
make fmt          # black + ruff --fix
make typecheck    # mypy
```

Pre-commit hooks (ruff, black, mypy) are configured in
`.pre-commit-config.yaml` — run `pre-commit install` once to enable them.

## Project layout

```
jaios/
├── backend/        # FastAPI + LangGraph + SQLAlchemy
├── frontend/        # Next.js dashboard
├── infra/
│   ├── docker/       # Dockerfiles (dev + production)
│   ├── init-db/      # Postgres init SQL
│   └── aws/terraform/ # AWS deployment skeleton — see docs/deployment-aws.md
└── docs/              # architecture + deployment docs
```

## Deploying to AWS

See [`docs/deployment-aws.md`](docs/deployment-aws.md) — a real, validated
Terraform skeleton (VPC, RDS+pgvector, ECR, ECS Fargate, ALB) plus
production Dockerfiles, with the known gaps (HTTPS, autoscaling) called out
explicitly rather than guessed at.

## Status

Phases 1–5 complete (local foundation, real workflows, tooling/worker
integrations, business-intelligence layer, hardening/cloud readiness) —
see `docs/architecture.md` for the full breakdown of what's implemented in
each phase, including the honest gaps (e.g. no HTTPS in the Terraform
skeleton, GitHub PR-creation approval declared but not yet wired into a
workflow node).

CI (`.github/workflows/ci.yml`) runs backend tests against a real
Postgres+pgvector service container, frontend typecheck/build, and
`terraform validate` on every push/PR. The full `docker compose up` path —
including a real multi-agent workflow run through a local Ollama model, the
DevOps approval pause/resume cycle, and an authenticated approval — has
been verified end-to-end; see the "Post-Phase-5 hardening" section of
`docs/architecture.md` for a real deadlock this caught and fixed.
