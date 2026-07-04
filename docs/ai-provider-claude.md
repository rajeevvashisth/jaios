# Configuring Claude / Anthropic

Claude is JAIOS's recommended default for reasoning-heavy work — company
planning, product/engineering strategy, compliance and finance reasoning,
and coding assistance (see [Operating modes & model routing](operating-modes.md)
for exactly which task types prefer it).

## Bring your own key (BYOK)

1. Go to **AI Settings → Providers → Add a provider**.
2. Choose **Anthropic (Claude)**.
3. Paste your API key (from [console.anthropic.com](https://console.anthropic.com)).
4. Optionally set a default model (defaults to `claude-sonnet-5` if left
   blank).
5. Save. The first provider of a given kind you add for a workspace
   becomes that kind's default automatically; you can change this later.

## What actually happens to the key

- It's encrypted (Fernet symmetric encryption) before being written to the
  database, using a server-wide `SECRET_ENCRYPTION_KEY` — see
  `backend/app/core/secrets.py` for the exact implementation.
- The API never returns the key once saved — the UI only ever shows
  "configured" / "not configured", never the value.
- **Limitation, stated plainly**: this is a single app-wide encryption key,
  not per-workspace envelope encryption or a real secrets manager (KMS/
  Vault). Anyone with both database access *and* the app's environment
  config can decrypt every workspace's stored keys. That's an acceptable
  tradeoff for a self-hosted v1 where you control both, but it is **not**
  a substitute for a real secrets manager if you're hosting JAIOS for
  other people. Rotating `SECRET_ENCRYPTION_KEY` requires re-encrypting
  existing rows — not automated yet.

## Without BYOK

If you never configure a workspace-level Anthropic key, JAIOS falls back
to whatever the server operator set via the `ANTHROPIC_API_KEY` /
`DEFAULT_LLM_PROVIDER` environment variables (this is how a single-tenant,
self-hosted deployment — like the original Jyka Labs LLP setup — runs
without ever touching AI Settings at all). BYOK and the global fallback
are mutually exclusive per workspace: as soon as one provider config
exists for a workspace, routing only considers what that workspace has
configured.

## Model choice

The default model is `claude-sonnet-5`. You can set a different
`default_model` per provider config in AI Settings if you want a specific
Claude model for that workspace.
