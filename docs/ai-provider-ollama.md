# Configuring Ollama (local / self-hosted)

Ollama runs models on your own machine or server — no API key, no data
leaving your infrastructure. JAIOS's router prefers it for local/cheap
tasks (document summarization, extraction, draft text) and for any
workspace running in **Privacy-first** or **Lowest cost** operating mode
(see [Operating modes & model routing](operating-modes.md)).

## Prerequisites

Install and run Ollama, then pull at least one model:

```bash
brew install ollama        # or see ollama.com for other platforms
ollama serve
ollama pull llama3.2:latest
```

## Configuring it in JAIOS

1. Go to **AI Settings → Providers → Add a provider**.
2. Choose **Ollama (local / self-hosted)**.
3. Set the **base URL** — this is the one setting people get wrong, because
   it depends on where the JAIOS *backend* process is actually running
   relative to Ollama:

   | Backend runs... | Ollama runs... | Base URL |
   |---|---|---|
   | Natively (`make backend-dev`) | Same machine | `http://localhost:11434` |
   | In Docker Compose | Natively on the host Mac/PC | `http://host.docker.internal:11434` |
   | In Docker Compose | In the bundled `ollama` service (`--profile local-models`) | `http://ollama:11434` |

   `localhost` inside a container refers to the container itself, not your
   host machine or a sibling container — this is the single most common
   misconfiguration here.
4. Set a default model — whatever `ollama list` shows you have pulled,
   e.g. `llama3.2:latest`.
5. Save.

## No API key needed

Ollama provider configs have no `api_key` field — only `base_url` and
`default_model`. Nothing is encrypted for Ollama configs because there's
no secret to protect; the base URL is stored as plain config.

## What quality to expect

Local models are meaningfully weaker than Claude at complex reasoning,
planning, and coding tasks — that's exactly why the router only sends
"local-tier" task types there by default (see the routing table in
[Operating modes & model routing](operating-modes.md)). JAIOS does not
oversell local model quality: if you pick **Highest quality** mode, every
task goes to your premium (Claude/OpenAI) provider instead, regardless of
what Ollama config you have.
