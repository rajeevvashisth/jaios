# JAIOS — Jyka AI Operating System — Phase 1 Architecture

Company-wide agentic operating system for Jyka Labs. This document covers the
Phase 1 (local foundation) design: architecture, folder structure, domain
model, agent registry, orchestration design, database schema, frontend
structure, and local infra. Code under `backend/` and `frontend/` implements
this design incrementally.

## 1. Overall Architecture

```
                              ┌─────────────────────────┐
                              │        Frontend         │
                              │   Next.js / React / TS  │
                              └────────────┬────────────┘
                                           │ REST (JSON)
                              ┌────────────▼────────────┐
                              │        FastAPI           │
                              │  api/routers/*  (HTTP)   │
                              └────────────┬────────────┘
                                           │
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
┌───────▼────────┐                ┌────────▼────────┐               ┌─────────▼────────┐
│  Domain Layer   │                │ Orchestration    │               │  Governance Layer  │
│  models/        │◄──────────────►│ Layer (LangGraph)│◄─────────────►│  approvals/perms/  │
│  schemas/       │                │ orchestration/   │               │  audit_log         │
│  services/      │                └────────┬────────┘               └───────────────────┘
└───────┬────────┘                          │
        │                          ┌────────▼────────┐
        │                          │  Agent Registry  │
        │                          │  agents/         │
        │                          └────────┬────────┘
        │                                   │
┌───────▼────────┐                ┌────────▼────────┐                ┌───────────────────┐
│  Memory Layer   │◄──────────────►│   Tool Layer     │◄──────────────►│  Knowledge / RAG   │
│  memory/        │                │   tools/         │                │  knowledge/        │
│  (Postgres +    │                │   (fs, terminal,  │                │  (pgvector search) │
│   pgvector)     │                │    git, docker)   │                └───────────────────┘
└─────────────────┘                └──────────────────┘

                              ┌────────────▼────────────┐
                              │   PostgreSQL + pgvector   │
                              └──────────────────────────┘
```

**Key decision: LangGraph orchestrates, specialized systems execute.** Agents
are LangGraph nodes that make decisions and call *tools* — they do not
directly shell out or hardcode integration logic. This keeps agents thin and
lets us swap a tool's implementation (e.g. local terminal → remote sandbox,
or a future MCP server) without touching agent or graph code.

**Why FastAPI + LangGraph + Postgres/pgvector instead of a more "batteries
included" agent framework:** the org needs a domain model (company, product,
project, task) that outlives any one agent framework. LangGraph is used only
for *orchestration* (state machine, checkpointing, human-in-the-loop), while
the domain and governance layers are framework-agnostic so they survive a
future orchestration engine swap.

## 2. Folder Structure

```
jaios/
├── README.md
├── docker-compose.yml
├── Makefile
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py                 # FastAPI app factory
│       ├── config.py               # Settings (pydantic-settings)
│       ├── core/                   # logging, llm provider abstraction
│       ├── db/                     # engine/session, declarative base
│       ├── models/                 # SQLAlchemy ORM models (domain)
│       ├── schemas/                 # Pydantic request/response models
│       ├── services/                # business logic, orchestrates models+repos
│       ├── api/routers/             # thin HTTP layer -> services
│       ├── agents/                  # agent registry + 8 core agent definitions
│       ├── orchestration/           # LangGraph state, graph, routing, checkpoints
│       ├── tools/                   # pluggable tool framework + concrete tools
│       ├── memory/                  # short/long-term memory store + embeddings
│       ├── knowledge/               # document ingestion + RAG retrieval
│       └── governance/              # permissions, approvals, audit log
│   └── tests/
├── frontend/                       # Next.js app router UI
├── infra/
│   ├── docker/                     # Dockerfiles
│   └── init-db/                    # pgvector extension bootstrap SQL
└── docs/
    └── architecture.md
```

Each top-level backend package (`models`, `agents`, `tools`, `memory`, ...)
is independently testable and has a single responsibility. No package
reaches directly into another package's internals — cross-package access
goes through the module's public functions/classes in `__init__.py`.

## 3. Backend Domain Model

Top-level entity is the **Company**; everything else hangs off it.

- **Company** — one row (single-tenant for now, designed so `company_id`
  foreign keys everywhere make multi-company trivial later).
- **Product** (business unit / portfolio item) — belongs to a Company.
  `type` (saas/platform/internal_tool/ai_product/other), `stage`
  (idea/building/live/sunset), `owner`, `status`.
- **Project** — belongs to a Product (or directly to the Company for
  cross-cutting initiatives). Has goals, status, dates.
- **Task** — belongs to a Project, optionally linked to an Agent (assignee)
  and a human owner. Has status, priority, due date, dependencies.
- **AgentDefinition** — registry row per agent (see §4).
- **WorkflowRun** — a LangGraph execution instance; stores thread id, graph
  name, status, initiating actor, linked task/project.
- **WorkflowStep** — individual node execution within a run (for traces).
- **ApprovalRequest** — a governance checkpoint tied to a WorkflowRun/step.
- **MemoryRecord** — structured memory row (see §7... memory layer).
- **KnowledgeDocument** / **KnowledgeChunk** — ingested docs + embedded
  chunks for RAG.
- **AuditLogEntry** — append-only log of every agent decision / tool call.

Relationships are intentionally simple (mostly 1:many via FK) — no generic
polymorphic "linkable" tables in Phase 1. `Task.product_id` /
`Task.project_id` are nullable FKs so a task can attach at whichever level
makes sense, rather than forcing an artificial Project wrapper for every
company-level task.

## 4. Agent Registry Design

Agents are defined in code (`app/agents/definitions.py`) as static
`AgentSpec` objects — a formal, typed structure so behavior is versioned in
git, not scattered in DB rows. The DB `AgentDefinition` table stores runtime
state (enabled/disabled, last active, config overrides) keyed by the same
`agent_key`, so the UI can inspect/toggle agents without redeploying code.

```python
class AgentSpec(BaseModel):
    key: str                     # "ceo", "cto", "developer", ...
    name: str
    layer: AgentLayer            # executive | technology | governance
    responsibility: str          # short description
    system_prompt: str
    allowed_tools: list[str]     # tool keys this agent may invoke
    memory_scope: MemoryScope    # company | product | project | agent-private
    can_delegate_to: list[str]   # agent keys this agent may hand off to
    requires_approval_for: list[str]  # action types needing human sign-off
    escalates_to: str | None     # agent key to escalate blocked work to
```

The **AgentRegistry** is a simple in-process dict keyed by `agent_key`,
populated at startup from `definitions.py`, exposing `get(key)`,
`list()`, `tools_for(key)`. This is intentionally *not* a database-driven
plugin system yet — 8 agents don't need one, and a registry that's just a
typed Python dict is trivially testable and diffable in review.

Adding agent #9 later = add one `AgentSpec` + one node function; no schema
migration required unless it needs new persistent state.

## 5. LangGraph Orchestration Design

One core module, `orchestration/graph.py`, builds a `StateGraph` per
**workflow type** (not one giant graph for everything). Shared pieces:

- **State** (`orchestration/state.py`): a `TypedDict`/Pydantic model carrying
  `messages`, `company_id`, `originating_task_id`, `context` (dict of
  agent outputs so far), `pending_approval` (set when a node needs a human).
- **Nodes** (`orchestration/nodes.py`): one node function per agent, built by
  wrapping the agent's `AgentSpec` — loads system prompt, calls the LLM
  provider, executes any tool calls via the tool layer, writes results into
  state, and appends an `AuditLogEntry`.
- **Routing** (`orchestration/routing.py`): conditional edges implementing
  each agent's `can_delegate_to` — e.g. CTO → {developer, devops, qa} based
  on task type, or CEO → {finance, operations, cto} for a portfolio review.
- **Checkpointing**: LangGraph's Postgres checkpointer persists state after
  every node, so long-running workflows survive a process restart — a
  prerequisite for a system meant to run unattended across a business day.
- **Human-in-the-loop**: nodes whose action type is in
  `requires_approval_for` raise an `interrupt()`; the graph pauses, an
  `ApprovalRequest` row is created, and the API exposes
  `POST /workflows/{run_id}/approve|reject` to resume the graph.

Phase 1 ships two runnable graphs as the reference pattern:
`workflows/task_delegation.py` (CEO → CTO → Developer/QA/DevOps → status
back to CEO) and `workflows/portfolio_review.py` (CEO fan-out to
Finance+Operations+CTO → consolidated report) — the other three example
workflows in the spec follow the same shape and are documented but not all
wired up in Phase 1 to avoid speculative graphs nobody runs yet.

## 6. Database Schema (Phase 1)

PostgreSQL, `pgvector` extension enabled via `infra/init-db/01-extensions.sql`.
Managed by Alembic migrations under `backend/alembic/versions/`.

```
companies(id, name, mission, strategic_goals(jsonb), created_at, updated_at)

products(id, company_id fk, name, type, stage, owner, status,
         description, roadmap(jsonb), created_at, updated_at)

projects(id, company_id fk, product_id fk null, name, goal, status,
         start_date, target_date, created_at, updated_at)

tasks(id, company_id fk, project_id fk null, product_id fk null,
      title, description, status, priority, assignee_agent_key null,
      assignee_human null, due_date, depends_on_task_id fk null,
      created_at, updated_at)

agent_definitions(agent_key pk, name, layer, enabled, config(jsonb),
                   last_active_at, created_at, updated_at)

workflow_runs(id, graph_name, thread_id, status, initiating_actor,
              company_id fk, task_id fk null, project_id fk null,
              started_at, completed_at)

workflow_steps(id, workflow_run_id fk, agent_key, step_index, input(jsonb),
               output(jsonb), status, started_at, completed_at)

approval_requests(id, workflow_run_id fk, workflow_step_id fk,
                   action_type, requested_by_agent_key, summary,
                   status (pending/approved/rejected), decided_by,
                   decided_at, created_at)

memory_records(id, scope_type (company/product/project/agent/task),
                scope_id, agent_key null, kind (short_term/long_term),
                content(jsonb), created_at, expires_at null)

knowledge_documents(id, company_id fk, title, source_type, source_uri,
                     ingested_at)

knowledge_chunks(id, document_id fk, chunk_index, content, embedding vector(1536),
                  metadata(jsonb))

audit_log_entries(id, occurred_at, actor_type (agent/human/system),
                   actor_key, action, target_type, target_id,
                   tool_used null, input(jsonb), output(jsonb), workflow_run_id fk null)
```

`memory_records.content` and `agent_definitions.config` use `jsonb` rather
than new tables per memory "kind" — Phase 1 memory shapes are still
changing; jsonb avoids a migration every time a new memory shape shows up,
while `scope_type`+`scope_id` keep it queryable and indexable.

## 7. Frontend Page Structure

Next.js App Router, one route segment per module, matching the spec's UI
list directly so the nav is a literal reflection of the system modules:

```
app/
├── page.tsx                 # Overview / Dashboard
├── agents/page.tsx          # Agent registry: roles, tools, status
├── tasks/page.tsx           # Task list/board across company
├── projects/page.tsx        # Projects, grouped by product
├── products/page.tsx        # Portfolio: products/business units
├── knowledge/page.tsx       # Document upload + search
├── memory/page.tsx          # Memory/activity browser
├── workflows/page.tsx       # Running/past workflow runs + approvals
├── logs/page.tsx            # Audit log / traces
└── settings/page.tsx        # Company profile, config
```

All pages talk to FastAPI through a single typed `lib/api.ts` client — no
per-page fetch boilerplate, and one place to add auth headers later.

## 8. Local Docker Compose Setup

```yaml
services:
  postgres:   # postgres:16 + pgvector, volume-backed, init SQL mounted
  backend:    # FastAPI + LangGraph, built from infra/docker/backend.Dockerfile
  frontend:   # Next.js dev server, built from infra/docker/frontend.Dockerfile
  # ollama is documented as an optional profile (local models) — not required to boot
```

Backend and frontend both support running outside Docker too (`uvicorn`
reload / `next dev`) for fast local iteration — Compose is for "run the
whole system," not the only way to develop.

## Phase 1 scope note

Everything above is designed to extend without rewrites: new agents are new
`AgentSpec` entries, new tools are new `Tool` subclasses registered in
`tools/registry.py`, new workflows are new graph-builder functions, and AWS
deployment later is a matter of swapping the Postgres connection string and
containerizing the same images — no architectural change.

## Phase 2 additions

Phase 2 fills in the "real workflows" gaps left open in Phase 1, with no
changes to the Phase 1 architecture — everything below is new modules and
new registry entries, not modified ones.

**Task routing.** `app/services/task_routing.py` adds
`suggest_agent_for_task()` / `route_task()` — a deterministic keyword-overlap
classifier that scores a task's title+description against each agent's
domain vocabulary (e.g. "deploy", "docker", "release" → DevOps; "regression",
"flaky" → QA) and assigns `assignee_agent_key` accordingly, exposed as
`POST /api/tasks/{id}/route`. Rule-based rather than an LLM call
deliberately: routing needs to be instant, free, and deterministic, and this
keeps it unit-testable without mocking an LLM. The signature is the seam for
swapping in an LLM classifier later if keyword matching proves too coarse.

**Three more reference workflows**, registered in `orchestration/graph.py`
alongside the Phase 1 pair:

- `compliance_review` — Legal → Operations → CEO notify (spec Example
  Workflow 3). Legal's node carries `action_type="legal_signature"`, so
  every run pauses for human sign-off before Operations picks up the
  obligation to track.
- `revenue_cost_review` — Finance → CEO (spec Example Workflow 4). A pure
  reporting workflow with no approval checkpoint, since nothing is spent or
  committed.
- `incident_response` — DevOps → CTO → **{Developer | QA}** → CEO status
  update (spec Example Workflow 5). This is the reference pattern for
  *conditional* routing: `orchestration/workflows/incident_response.py`
  defines `route_incident(state)`, a routing function passed to
  LangGraph's `add_conditional_edges`, which inspects the CTO node's output
  for regression/flaky-test signals and picks the next node accordingly —
  unlike the Phase 1 workflows' fixed linear/fan-out shape, the path here
  depends on what an upstream agent actually said.

**Deeper trace visibility.** A new dynamic route,
`frontend/app/workflows/[runId]/page.tsx`, renders a single run's full step
timeline (agent, status, timestamps, output) plus an inline approve/reject
control when that run is paused on an approval — the Workflows list page
links each run into this view instead of only listing run-level status.

**Portfolio CRUD in the UI.** Products, Projects, and Tasks pages gained
create forms (they were previously read/API-only in Phase 1), and the Tasks
page adds per-row "Route" and "Start workflow" actions so a task can be
assigned and pushed into `task_delegation` without leaving the browser.

## Phase 3 additions

Phase 1/2's `build_agent_node` gives every agent a single LLM turn — fine
for planning/reporting/reviewing roles, but Developer and QA are supposed to
*do* something verifiable (write code, run tests), not just describe it.
Phase 3's central change is giving those two roles real tool execution
inside the graph; everything else (coding worker, GitHub, QA runner) is the
tooling that execution needed.

**Specialized nodes with real tool execution.**
`orchestration/specialized_nodes.py` adds `build_developer_node()` and
`build_qa_node()`, used in place of the generic node for Developer and QA in
both `task_delegation` and `incident_response`:

- Developer plans with the LLM (as before), then hands that plan to the
  `coding_worker` tool to actually attempt the implementation. The worker's
  success/output is recorded alongside the plan — a missing coding tool
  produces a truthful "unavailable" step, not a silent no-op or a crash.
- QA plans a test approach, then actually runs the project's pytest suite
  via the `qa_test_runner` tool and records structured pass/fail counts —
  a real quality gate, not an LLM's unverified opinion that tests pass.
- `route_after_qa()` is a new conditional edge in `task_delegation`: a
  genuine test failure loops back to Developer, up to `MAX_QA_RETRIES` (2)
  rounds, before proceeding to DevOps regardless — a bounded retry loop so
  an unfixable or flaky test can't wedge a run forever. `qa_retry_count` and
  `workspace_path` (the directory these tools operate in, defaulting to
  `WORKSPACE_ROOT`) are new `WorkflowState` fields; callers can point
  `workspace_path` at a real checked-out repo via `WorkflowStartRequest`.

**Claude Code / OpenHands coding worker pattern.**
`tools/workers/` defines a `CodingWorker` ABC plus two implementations —
`ClaudeCodeWorker` (shells out to the `claude` CLI in print mode) and
`OpenHandsWorker` (same pattern for OpenHands' headless mode) — both
returning a failed (not raised) result when their binary isn't installed,
so a machine without either tool degrades gracefully rather than crashing a
workflow. `tools/coding_worker_tool.py` wraps whichever backend
`CODING_WORKER_BACKEND` selects behind one `coding_worker` tool key, so the
Developer node never knows which backend is running.

**GitHub support.** `tools/github_tool.py` wraps the `gh` CLI with an
allowlisted subcommand set split into read-only (`pr list/view/diff`,
`issue list/view`, ...) and write (`pr create`, `pr comment`, `pr merge`,
...) — added to Developer's and DevOps' `allowed_tools`. The tool itself
only enforces the allowlist; write-vs-read is a distinction the *workflow*
is meant to act on via `requires_approval_for` (Developer now requires
approval for `github_pr_create`, the same pattern as DevOps' `deploy`). No
graph currently wires a PR-creation node, so today this is available,
tested infrastructure rather than an end-to-end enforced path — the same
honest caveat Phase 1 noted for `finance_payment` before `revenue_cost_review`
existed.

**QA execution hooks.** `tools/qa_runner_tool.py` runs pytest via
`sys.executable -m pytest` (not a bare `python3` off PATH, so resolution is
unambiguous regardless of how many Pythons are on the host) and parses
passed/failed/error counts out of pytest's summary line — this is what
`build_qa_node()` calls, and what `route_after_qa` keys its retry decision
off of.

**Verification note.** This phase was validated against a real
Postgres 17 + pgvector instance (not just the skip-when-unreachable path),
which caught two real bugs before they shipped: the test fixture wasn't
seeding `agent_definitions`, so any test assigning a task to an agent hit a
foreign-key violation (fixed by seeding the registry in `conftest.py`,
mirroring what app startup already does); and a node test held onto an ORM
object across the node's own `db.close()`, hitting a `DetachedInstanceError`
(fixed by capturing the id before invoking the node). Worth remembering
next time DB-backed tests all skip locally — a green skip isn't the same as
a green pass.

## Phase 4 additions

Phase 4 is the business-intelligence layer: finance dashboards, compliance
reminders, operations/portfolio reporting, and a CEO summary view. Unlike
Phases 1–3, this is mostly new domain data and deterministic aggregation —
dashboards need to render even with no LLM configured, so none of it is
gated behind an agent call.

**New domain models** (`models/finance.py`, `models/compliance.py`,
migration `0002_finance_and_compliance`):

- `FinanceEntry` — a revenue or expense line, optionally attached to a
  product. Amounts are stored as integer minor units (`amount_cents`), not
  float, so aggregation never accumulates rounding error. Phase 4 assumes a
  single operating currency per company — no FX conversion — a documented
  simplification, not an oversight.
- `ComplianceObligation` — a due-date-bound obligation (tax filing,
  trademark renewal, contract renewal) owned by Finance or Legal. Urgency
  (`overdue`/`due_soon`/`upcoming`/`completed`) is deliberately **not** a
  stored column — `services/compliance_service.py` derives it from
  `due_date` at read time, so it can never go stale between requests. Only
  `completed` is persisted, since that's a real user action.

**Deterministic aggregation services**, no LLM involved:

- `finance_service.summarize_finances()` — revenue/expense/margin, with a
  per-category breakdown, scopable by product and date range.
- `compliance_service` — urgency computation plus list/complete operations.
- `reports_service.get_ceo_summary()` — the single call backing both the
  Overview dashboard and (via the Finance/Compliance pages' "ask the agent"
  buttons) a real-numbers-grounded workflow goal: portfolio status per
  product, company finance summary, operations health (open/overdue/blocked
  tasks, active runs, pending approvals), compliance obligations overdue/due
  soon, and the last 10 workflow runs.
- `reports_service.get_product_status_report()` — the same shape scoped to
  one product, backing the new product detail page.

**Grounding agent narratives in real numbers, without backend
special-casing.** Rather than have the backend inject computed figures into
a workflow's state (which would special-case `revenue_cost_review` by graph
name), the Finance and Compliance pages compute the goal string client-side
from the real `FinanceSummary`/`ComplianceObligation` data before calling
`POST /workflows/start` — so "Ask Finance Agent for a narrative" hands the
Finance/CEO agents actual revenue and expense figures instead of letting
them work from a human-typed, potentially inaccurate description.

**New routers**: `finance.py` (`/finance/entries`, `/finance/summary`),
`compliance.py` (`/compliance/obligations`, `.../complete`), `reports.py`
(`/reports/ceo-summary`, `/reports/product-status/{id}`).

**Frontend**: two new nav items, Finance and Compliance, plus a product
detail page (`/products/[productId]`) rendering
`ProductStatusReport`. The Overview page now renders the full CEO summary
(finance snapshot, portfolio table, compliance due-soon/overdue, recent
workflow runs) instead of three plain stat cards.

**Verification note.** Re-validated end-to-end against a real Postgres 17 +
pgvector instance again this phase (76/76 passing, zero skips), including
the new migration applying cleanly on top of Phase 1's.

## Phase 5 additions — hardening / cloud readiness

The original plan's Phase 5 ("Hardening / Future Cloud Readiness") bundles
five distinct concerns — AWS deployment, multi-user support, external auth,
broader tool integrations, stronger observability — into one phase. It's
split here into three sub-phases (5A/5B/5C) so each lands as an
independently reviewable, independently verified change.

### 5A — Observability

- `core/metrics.py` — five Prometheus counters/histograms:
  `jaios_http_requests_total`/`_duration_seconds`, `jaios_agent_turns_total`,
  `jaios_tool_calls_total` (labeled success/failure/**denied** — a spike in
  denials is as alertable as a spike in failures), `jaios_workflow_runs_total`,
  `jaios_approval_decisions_total`. Exposed at `GET /metrics` in standard
  Prometheus text format.
- `core/middleware.py` — `ObservabilityMiddleware` assigns a request ID
  (returned as `X-Request-ID`, honoring a client-supplied one if present),
  binds it into every structlog line for that request via
  `structlog.contextvars`, and records the request-count/latency metrics
  above using the matched route's path *template* (`/tasks/{task_id}`) —
  not the raw URL — so per-path series don't explode into one per unique ID.
- `GET /health` now actually checks the database (`SELECT 1`) and reports
  `degraded` if it fails, instead of always returning `ok` unconditionally.
- Structured log lines added at the points an operator actually cares about:
  `tool_call`/`tool_call_denied`, `agent_turn`, `approval_requested`/
  `approval_decided`, `workflow_run_finished`, `http_request`.
- This composes with the Phase 1 audit log rather than replacing it:
  metrics answer "is something wrong right now" (aggregate rates, cheap to
  alert on); the audit log answers "what exactly happened" (per-action
  detail, queryable after the fact). Langfuse or an equivalent LLM-trace
  tool would slot in alongside both, at the `plan_with_llm` call site — not
  wired up here since it's optional per the original spec.

### 5B — Auth & multi-user readiness

- `models/user.py` — a `User` belongs to exactly one company; `role` is
  `admin`/`member`/`viewer`, a coarse floor for **human** actions, entirely
  separate from agents' tool/approval permissions (`AgentSpec`). The first
  user registered for a company becomes its admin (standard self-hosted-app
  bootstrap); everyone after that is a `member`.
- `core/security.py` — bcrypt password hashing, JWT issuance/verification
  (`PyJWT`, HS256). `JWT_SECRET_KEY` defaults to an obviously-insecure dev
  value that must be overridden before any non-local deployment (enforced
  by convention/docs, not by code — there's no production-detection to
  gate on yet).
- `api/deps.py` — `get_current_user` (Bearer token → `User`, 401 on
  missing/invalid/expired) and `require_role(*roles)`, a dependency
  factory: `Depends(require_role("admin", "member"))`.
- **The one endpoint actually gated so far**: `POST
  /workflows/{run_id}/approve` now requires `admin` or `member`, and —
  more importantly — `decided_by` is no longer a client-supplied string in
  the request body (trivially spoofable) but is derived from
  `current_user.email`. Every other Phase 1-4 endpoint remains open, matching
  this system's local-first, single-operator positioning; `require_role`
  is there to apply broadly once there's a real second user who
  shouldn't see everything.
- **Frontend**: `lib/auth-context.tsx` + `/login` page (register/sign-in),
  token persisted to `localStorage` and attached automatically by
  `lib/api.ts`'s `request()` — this was a required fix, not an add-on:
  once the backend stopped trusting client-supplied `decided_by`, the
  existing approve/reject buttons would have started 401ing without it.

### 5C — Cloud deployment readiness

- **Production Dockerfiles** (`infra/docker/*.prod.Dockerfile`), separate
  from the dev ones Compose uses: multi-stage, non-root, no editable
  installs or dev extras. The frontend one switched to `node:22-alpine`
  after IDE vulnerability scanning flagged `node:20-slim` (27 high + 1
  critical → 2 high) and uses Next.js `output: "standalone"` for a minimal
  runtime image. **Important nuance documented in the Dockerfile itself**:
  every frontend page is a client component reading
  `NEXT_PUBLIC_API_BASE_URL` at fetch time, and Next.js inlines
  `NEXT_PUBLIC_*` vars into the client bundle at *build* time — it must be
  a `--build-arg`, not a runtime container env var, or the deployed
  frontend silently keeps pointing at whatever URL it was built with.
- **`infra/aws/terraform/`** — a real, `terraform validate`-clean skeleton:
  VPC (via the `terraform-aws-modules/vpc/aws` registry module), RDS
  Postgres 16 (pgvector needs no special parameter group — Alembic's
  `CREATE EXTENSION IF NOT EXISTS vector` just works), ECR ×2, an ALB
  routing `/api/*`+`/health`+`/metrics`+`/docs` to the backend target
  group and everything else to the frontend, ECS Fargate services for
  both, Secrets Manager for `DATABASE_URL`/API keys/JWT secret, and
  separate execution vs. task IAM roles. Deliberately incomplete where a
  guessed default would be worse than an explicit TODO: no HTTPS listener
  (needs a real domain + ACM cert), no autoscaling, single NAT gateway. See
  `docs/deployment-aws.md` for the full known-gaps list and the actual
  build/push/rollout steps.
- **`tools/slack_tool.py`** — a concrete instance of the "future tool
  categories" pattern (Slack/Jira/email/CRM/...) the architecture doc
  called out but hadn't built: posts to a Slack incoming webhook, no SDK
  dependency, gracefully returns a failed result (not an exception) when
  `SLACK_WEBHOOK_URL` isn't configured. Added to the Operations agent's
  `allowed_tools`.

**Verification note.** Same standard as every prior phase: 99/99 backend
tests passing against a real Postgres 17 + pgvector instance (zero skips),
clean `ruff`/`black`/`mypy`, clean frontend `tsc`/`next build`, and — new
this phase — `terraform init`/`fmt`/`validate` clean against the actual AWS
provider schema (network access confirmed; no AWS account was used, so
nothing was actually `apply`'d).

## Post-Phase-5 hardening: a real bug only Docker Compose could have found

Every phase up to this point was verified against a real Postgres, but
never against the actual `docker compose up` path, and never with a real
LLM call driving a full graph. Doing both for the first time (via
[colima](https://github.com/abiosoft/colima) — this machine had no Docker —
plus a local Ollama model, so no paid API key was needed) surfaced a
genuine, previously-undetected bug:

**The bug.** `orchestration/checkpoints.py`'s `get_checkpointer()` was
called lazily, on first use, from inside a request handler
(`workflow_service.start_workflow`). Its one-time `PostgresSaver.setup()`
runs `CREATE INDEX CONCURRENTLY`, which — by Postgres design — blocks until
every other open transaction on the database finishes. But
`start_workflow`'s own `db` session was sitting idle-in-transaction at that
exact moment (`db.refresh(run)` opens an implicit transaction that nothing
had closed yet), because the request was still waiting on the very
`get_checkpointer()` call it triggered. The request waited on `setup()`;
`setup()` waited on the request's own idle transaction. A permanent
self-deadlock — on the very first workflow anyone ever starts, in any fresh
deployment. No unit test caught this because no test had ever actually
compiled a graph against a real checkpointer (`get_graph()` was only ever
exercised through `available_graphs()`, which doesn't touch the
checkpointer at all).

**The fix**, two parts:

1. `main.py`'s `lifespan` now calls `get_checkpointer()` eagerly at
   startup, alongside the existing `sync_agent_definitions` call — so
   `setup()` runs once, before any request can be holding a transaction
   open.
2. `workflow_service.start_workflow`/`resume_workflow` now call `db.commit()`
   immediately before invoking the graph, closing out the transaction
   `db.refresh()`/`db.get()` opened — so the request's own session is never
   idle-in-transaction across a graph run (which can take as long as
   several LLM calls), independent of the startup fix.

A new regression test, `test_all_graphs_compile_against_a_real_checkpointer`
in `tests/test_orchestration.py`, at least proves graph compilation itself
still works — though reproducing the concurrency scenario needs a live
server, which is exactly what caught it in the first place. **Lesson
generalized**: "all tests pass" and "never actually run for real" are both
true statements that can coexist, and the gap between them is exactly where
bugs like this hide.

After the fix, verified for real end-to-end against the live Docker Compose
stack + a local Ollama model (`qwen2.5:0.5b`, no API key required):
company/user creation, register/login/`/me`, a full `revenue_cost_review`
run (Finance → CEO, each genuinely reading the prior agent's real LLM
output), and a full `task_delegation` run through all six nodes including
the DevOps approval interrupt — paused, approved by an authenticated user
(`decided_by` correctly derived from the token, not client input), and
resumed to completion. The QA node's `qa_test_runner` tool call and the
Developer node's `coding_worker` tool call (failed gracefully — no `claude`
CLI in the container, exactly as designed) both showed up in the audit log
and in `/metrics` as expected.
