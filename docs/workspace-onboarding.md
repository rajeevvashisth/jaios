# Workspace onboarding

How a brand-new company starts using JAIOS, end to end.

## The bootstrap sequence

Two things have to exist before anyone can sign in: a workspace and a
company. There's a deliberate chicken-and-egg exception for this one step
— `POST /companies` works without being signed in (the same reasoning as
`/auth/register` being open: there's no account to authenticate as yet).

1. **Create your company** (Settings page, or `POST /companies` with just
   a `name`). This auto-creates a new workspace named after the company —
   you don't fill in a separate "workspace name" field unless you want to
   rename it later.
2. **Register your account** against that company (Login page → Register).
   The first person to register becomes `admin`; everyone after that
   defaults to `member`.
3. From here on, everything requires being signed in — see the sign-in
   prompt that appears on every page except Login and Settings if you're
   logged out.

## Filling in company context

Settings → **Legal / jurisdiction profile**: entity type, country,
jurisdiction/state, base currency. These drive:

- which compliance framework template is relevant (currently: a seeded
  India-LLP checklist — see [Compliance register](#), other jurisdictions
  are not yet templated and should be added as plain compliance items).
- what currency finance entries are denominated in.

Leave anything you're not sure about blank. JAIOS's compliance/finance
modules are built around never fabricating a fact you haven't confirmed —
an unset field is a request for input, not a bug.

## Adding a second company to the same workspace

If you're running more than one business under one operator (the same
BYOK keys, the same operating mode/budget), add a second company under
the existing workspace rather than creating a new one:

```
POST /companies
{ "name": "Second Co", "workspace_id": "<your workspace id>" }
```

This requires being signed in as a member of that workspace — an
anonymous caller can only create a *brand new* workspace, never attach a
company to one they don't already belong to.

## Adding your first product

Products → Add product. Fill in type/stage/owner/description as you know
them. If it's a real codebase, set its local workspace path — this is the
default working directory workflows use when you start one scoped to that
product, but note that a containerized backend needs an explicit bind
mount to actually read/write a host path; without it, the product record
still works for tracking tasks, finance, and compliance, just not
filesystem-level agent actions.

## Configuring AI

See [Configuring Claude](ai-provider-claude.md) and
[Configuring Ollama](ai-provider-ollama.md). Not required to start using
JAIOS — everything works against the server's global fallback provider
until you set up BYOK.

## What you get after onboarding

A working Command Center (dashboard) showing your portfolio, finance
summary, and open compliance items; a Tasks/Workflows surface to start
your first agent-run workflow; and an AI Settings page showing exactly
which provider/model handled each recent call.
