# What is JAIOS?

JAIOS (AI Operating System) is a platform for running a company — not just
chatting with an AI about it. Where a typical AI wrapper gives you a
conversation window bolted onto your existing tools, JAIOS gives you a
structured operating system: companies, products, tasks, workflows,
finance, and compliance all live as real, queryable data, and a small team
of role-specific AI agents (CEO, CTO, Developer, QA, DevOps, Finance,
Legal, Operations) act on that data through governed, auditable workflows.

## Who it's for

- Founder-led startups that want AI doing real operational work, not just
  answering questions about it.
- Small product companies and agencies running more than one product or
  business unit.
- Technical founders who want to bring their own model (Claude, a
  self-hosted Ollama model, or both) rather than being locked into one
  vendor.
- Anyone who wants a paper trail: every agent decision, tool call, and
  human approval is recorded, not just the final answer.

## The core hierarchy

```
Workspace                  ← your tenant boundary — one workspace per
 └─ Company                  customer/operator, can hold more than one company
     ├─ Product / Business Unit
     ├─ Task
     ├─ Workflow run
     ├─ Finance entry
     ├─ Compliance obligation
     └─ Knowledge document
```

A **workspace** is where AI provider configuration (BYOK keys, operating
mode, budgets) lives — that's shared infrastructure for whoever runs the
workspace, not duplicated per company. A **company** is a real legal/
business entity with its own jurisdiction, currency, and compliance
context. A **product** is what that company builds or operates.

## What JAIOS actually does today

- Runs multi-agent workflows (task delegation, portfolio review,
  compliance review, revenue/cost review, incident response) with a real
  human-approval gate for irreversible actions (deploys, payments, legal
  signatures).
- Tracks finance as a lightweight ledger — revenue, expense, and capital
  entries, categorized, with vendor/payment/proof metadata — not a full
  accounting system.
- Tracks compliance as a register with an honest applicability model: an
  obligation is either `applicable`, `not_applicable`, or
  `review_pending` — JAIOS never invents a due date or a "completed"
  filing it doesn't actually know about.
- Routes each AI call to whichever configured provider/model tier fits the
  task (see [Operating modes & model routing](operating-modes.md)) instead
  of always using the single most expensive model.
- Lets a workspace bring its own Claude API key, its own Ollama endpoint,
  or both (see [Configuring AI providers](ai-providers.md)).

## What it deliberately does not try to be

- Not a full accounting or ERP system — the finance/compliance modules are
  "lite" by design (see [Product scope](#) in the main README).
- Not a substitute for actual legal/tax/compliance advice — compliance
  items it can't verify are marked for human review, never fabricated.
- Not a chatbot skin over a single model — the AI is embedded in
  structured workflows with real data behind them, and you choose which
  provider does the work.

Continue to the [Quick Start](quickstart.md) to get a workspace running.
