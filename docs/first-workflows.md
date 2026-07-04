# First workflow examples

Four concrete things to try in your first session, in order of how quickly
you'll see something useful.

## 1. Add an expense

Finance → fill in the form: type (`expense`), category, amount, date. If
it's a real bill, add the vendor, payment status, and a proof/invoice
reference — these are separate fields specifically so a real audit trail
exists later, not just a lump amount.

Founder/investor money going *into* the company is a `capital` entry, not
`revenue` — JAIOS keeps these separate everywhere (summaries, margin
calculations) so a funding round never quietly inflates your apparent
revenue.

## 2. Create a compliance item

Compliance → **Seed standard India LLP compliance checklist** (if you're
an Indian LLP) populates the common categories (MCA/ROC filings, income
tax, GST, TDS, trademark, local registrations) as `review_pending` —
nothing is marked applicable or given a due date until you or your CA
confirm it applies. You can also add one manually with **Add obligation**
for anything jurisdiction-specific.

## 3. Ask JAIOS to plan a feature

Workflows → **Start workflow** → pick `task_delegation`, describe the goal
(e.g. "Ship a CSV export for the finance ledger"), optionally attach a
task or product. This runs CEO → CTO → Developer → QA → DevOps in
sequence, each agent building on the last one's output, with a real human
approval gate before DevOps' deploy step (see the **Pending approvals**
section on the Workflows page). Watch the step trace on the run's detail
page — every agent turn is recorded, along with which provider/model
handled it.

## 4. Ask for a portfolio review

Workflows → **Start workflow** → `portfolio_review` (goal: e.g. "How's the
product portfolio looking this month?"). This is the CEO-level
company_planning task type — it'll route to your premium provider tier by
default (see [Operating modes & model routing](operating-modes.md)) and
pull from your actual task/finance/compliance data rather than asking you
to re-describe your company in the prompt.

## Other things worth trying

- **Route a task automatically**: Tasks → any task → **Route** assigns it
  to the best-fit agent by keyword matching (deploy → DevOps, flaky test →
  QA, trademark → Legal, invoice → Finance), before you ever start a full
  workflow.
- **Ingest a document**: Knowledge → paste in an SOP or onboarding doc,
  then search it — this is what "AI should retrieve from the knowledge
  base instead of re-sending huge context" (see
  [AI usage optimization](ai-usage-optimization.md)) actually looks like
  from the product side.
