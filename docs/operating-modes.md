# Operating modes & model routing

Every AI call JAIOS makes goes through a router (`backend/app/services/model_router.py`)
that decides which provider and model actually handle it. This is a plain,
inspectable table lookup — not a learned or adaptive system, and not
magic. You can read the whole policy in that one file.

## The two things routing considers

1. **Task type** — what kind of work this is (see the table below). Each
   task type has a natural "tier": `premium` (best available reasoning) or
   `local` (cheap/local).
2. **Operating mode** — a workspace-level setting (AI Settings → Operating
   mode) that can either respect each task's natural tier, or force every
   task to one tier regardless of type.

| Operating mode | Effect |
|---|---|
| **Balanced** (default) | Each task uses its own natural tier — reasoning-heavy work goes premium, drafts/summaries go local. |
| **Highest quality** | Every task forced to the premium tier, even simple ones. |
| **Lowest cost** | Every task forced to the local tier, even complex ones — expect weaker output on reasoning-heavy tasks. |
| **Privacy-first / local-first** | Same effect as Lowest cost today (everything local) — the distinct "send nothing external, ever" enforcement is not yet a separate hard guarantee, just the practical effect of always picking a local provider. |

## Task type → natural tier

| Task type | Tier | Used by |
|---|---|---|
| `company_planning` | premium | CEO agent |
| `product_feature_planning` | premium | CTO agent |
| `coding_assistance` | premium | Developer, QA, DevOps agents |
| `compliance_summary` | premium | Legal agent |
| `finance_summary` | premium | Finance agent |
| `workflow_followup_draft` | local | Operations agent |
| `document_summary` | local | — |
| `document_extraction` | local | — |
| `expense_categorization` | local | — |
| `knowledgebase_qa` | local | — |
| `general_chat` | local | anything unmapped |

## How a provider actually gets picked

1. Resolve the tier (task type + operating mode, per the tables above).
2. Look at the workspace's *enabled* provider configs. If one is marked
   default **and** matches the resolved tier, use it.
3. Otherwise use any enabled config that matches the tier.
4. If nothing matches the tier at all, fall back to whatever the workspace
   *does* have configured (better than silently ignoring BYOK setup) or,
   if the workspace has no provider configs whatsoever, fall back to the
   server's global default — this is what makes a workspace that's never
   touched AI Settings behave exactly as it always has.

## What this does *not* do (yet)

- No per-request quality scoring or automatic escalation ("try local
  first, retry with premium if it looks wrong") — that's real future work,
  not implemented.
- No hard budget enforcement — monthly/daily budgets (AI Settings) are
  tracked and will be surfaced in usage views, but a request is never
  blocked for exceeding them in v1. Treat them as visibility, not a cap.
- No cross-provider prompt caching yet.

See [AI usage optimization](ai-usage-optimization.md) for the cost-control
techniques that *are* in place.
