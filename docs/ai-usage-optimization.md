# AI usage optimization

What JAIOS actually does today to avoid burning tokens and money, stated
plainly — including what's *not* built yet, so you're not left guessing.

## What's real and working

**Model routing by task type.** Every agent call is tagged with a task
type (`company_planning`, `coding_assistance`, `document_summary`, etc.)
and routed to whichever configured provider/model tier fits — see
[Operating modes & model routing](operating-modes.md). This is the
biggest lever: routing everyday summarization/draft work to a local Ollama
model instead of Claude, while keeping Claude for the reasoning-heavy
tasks that actually need it.

**A real knowledge base instead of re-pasting documents.** Knowledge →
ingest a document once; it's chunked and embedded (pgvector), and agents
retrieve relevant chunks by similarity search rather than the whole
document being re-sent in every prompt that might need it.

**Structured data instead of prose context.** Company, product, task,
finance, and compliance state live as real rows, not as accumulated free
text — an agent asks the database for what it needs (e.g. the finance
summary endpoint) instead of the whole history being retold in natural
language every time.

**Usage visibility.** AI Settings → Usage shows total calls, token counts
(where the provider reports them — see the note on Ollama below), and a
breakdown by provider and task type, logged from `AIUsageRecord` per call.
This is the honesty mechanism: if routing isn't behaving the way you
expect, this is where you'd see it.

**BYOK to a genuinely free local model.** Ollama costs nothing per call
once it's running — the cheapest possible "optimization" for any task
that tolerates a weaker model.

## What's tracked but not yet enforced

**Budgets are soft caps.** AI Settings lets you set a monthly/daily budget;
usage is logged against the workspace, but no request is currently blocked
for exceeding it. Treat this as visibility today, not a spending limit.

## What's genuinely not built yet

Said directly, because claiming otherwise would be exactly the kind of
overselling this product is trying not to do:

- **No context compression/summarization of prior workflow state.** A
  multi-agent workflow's later agents currently receive the full set of
  prior agents' raw outputs verbatim (see `plan_with_llm` in
  `backend/app/orchestration/nodes.py`) — there's no size-based
  summarization step yet. For today's workflow lengths (a handful of
  agent turns) this hasn't been a problem in practice, but it will not
  scale gracefully to much longer workflows without one.
- **No caching/reuse of repeated summaries** across calls.
- **No automatic escalation** ("try a cheap model, retry with a better one
  if the output looks wrong") — routing is decided once, up front, per
  task type.
- **No token-count-based dynamic routing** (e.g. "this context is huge,
  downgrade the model") — routing only looks at task type and operating
  mode, not actual prompt size.

If any of these matter for your workload, they're the natural next things
to build on top of `model_router.py` and `plan_with_llm` — both are
intentionally small and readable specifically so that's tractable.
