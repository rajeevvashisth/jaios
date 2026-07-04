# Quick Start (about 15 minutes)

This gets a fresh JAIOS workspace running locally with Docker, with your
first company, product, and AI provider configured.

## 1. Prerequisites (2 min)

- Docker + Docker Compose.
- One of: an Anthropic API key, an OpenAI API key, or a running
  [Ollama](https://ollama.com) install (`ollama serve`) — you can also add
  these later from the AI Settings page instead of at install time.

## 2. Start the stack (3 min)

```bash
git clone <this repo>
cd jaios
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 (interactive API docs at `/docs`)
- Frontend: http://localhost:3000

The backend runs its database migrations automatically on startup — there's
nothing to run by hand.

## 3. Create your workspace and company (3 min)

1. Open http://localhost:3000 — you'll land on **Settings**.
2. Fill in **Create a company** with your company's name. This bootstraps
   a new workspace (named after your company) and the company itself in
   one step — that's the only account-creation step that doesn't require
   being signed in yet, the same way signing up for anything starts
   unauthenticated.
3. Go to **Settings → Legal / jurisdiction profile** (only visible once
   you're signed in — see step 4) and fill in entity type, country,
   jurisdiction, and currency if you want compliance/finance features to
   reflect them accurately. Leave anything unknown blank rather than
   guessing — JAIOS treats blanks honestly instead of fabricating detail.

## 4. Create your account (2 min)

Go to **Sign in** in the top bar → **Register** → pick the company you just
created. The first person to register against a company becomes its
`admin`; everyone after that is a `member` by default. Almost every page in
JAIOS requires being signed in — the only exceptions are the login page
itself and the company-bootstrap step above.

## 5. Configure an AI provider (3 min)

Go to **AI Settings**:

- **Claude/Anthropic or OpenAI**: paste your API key. It's encrypted
  before being stored — see [Configuring AI providers](ai-providers.md)
  for exactly what that does and doesn't protect against.
- **Ollama**: point it at your Ollama endpoint (`http://localhost:11434`
  if it's running on the same machine as your browser, or
  `http://host.docker.internal:11434` if the *backend* needs to reach a
  host-native Ollama from inside Docker).

Pick an **operating mode** (Balanced is the sensible default — see
[Operating modes & model routing](operating-modes.md)).

If you skip this step entirely, JAIOS falls back to whatever provider the
server operator configured globally (or nothing, if none was set) — you
won't lose functionality, you just won't have BYOK routing yet.

## 6. Add your first product (2 min)

Go to **Products → Add product**. If it's a real local codebase, add its
local path — you'll need to grant the backend container filesystem access
to that path before agents can act on it directly (a bind mount); without
that, the product record still works for tracking tasks, finance, and
compliance.

## 7. Try your first workflow

See [First workflow examples](first-workflows.md) for four concrete things
to try right now: plan a feature, add an expense, create a compliance
item, and ask JAIOS for a portfolio review.
