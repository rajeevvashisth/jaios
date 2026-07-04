"use client";

import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AIProviderConfig,
  type AIProviderKind,
  type AIUsageSummary,
  type OperatingMode,
  type Workspace,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const PROVIDERS: { value: AIProviderKind; label: string; needsKey: boolean; needsUrl: boolean }[] = [
  { value: "anthropic", label: "Anthropic (Claude)", needsKey: true, needsUrl: false },
  { value: "openai", label: "OpenAI", needsKey: true, needsUrl: false },
  { value: "ollama", label: "Ollama (local / self-hosted)", needsKey: false, needsUrl: true },
];

const OPERATING_MODES: { value: OperatingMode; label: string; description: string }[] = [
  {
    value: "balanced",
    label: "Balanced",
    description: "Each task uses whichever tier (premium reasoning or local/cheap) fits it best.",
  },
  {
    value: "highest_quality",
    label: "Highest quality",
    description: "Every task goes to your best-configured reasoning provider, regardless of cost.",
  },
  {
    value: "lowest_cost",
    label: "Lowest cost",
    description: "Every task prefers your cheapest/local provider, even ones that'd normally reason harder.",
  },
  {
    value: "privacy_first",
    label: "Privacy-first / local-first",
    description: "Every task prefers a local provider (e.g. Ollama) so data stays on your infrastructure.",
  },
];

export default function AISettingsPage() {
  const { user } = useAuth();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [providers, setProviders] = useState<AIProviderConfig[]>([]);
  const [usage, setUsage] = useState<AIUsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [monthlyBudget, setMonthlyBudget] = useState("");
  const [dailyBudget, setDailyBudget] = useState("");
  const [savingBudget, setSavingBudget] = useState(false);

  const [provider, setProvider] = useState<AIProviderKind>("anthropic");
  const [displayName, setDisplayName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [defaultModel, setDefaultModel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!user) return;
    try {
      const ws = await api.workspaces.getMine();
      setWorkspace(ws);
      setMonthlyBudget(ws.monthly_budget_cents != null ? String(ws.monthly_budget_cents / 100) : "");
      setDailyBudget(ws.daily_budget_cents != null ? String(ws.daily_budget_cents / 100) : "");
      const [providerList, summary] = await Promise.all([
        api.ai.listProviders(ws.id),
        api.ai.usageSummary(ws.id),
      ]);
      setProviders(providerList);
      setUsage(summary);
    } catch (err) {
      setError(String(err));
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAddProvider(e: React.FormEvent) {
    e.preventDefault();
    if (!workspace) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.ai.createProvider({
        workspace_id: workspace.id,
        provider,
        display_name: displayName || undefined,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
        default_model: defaultModel || undefined,
        is_default: providers.filter((p) => p.provider === provider).length === 0,
      });
      setDisplayName("");
      setApiKey("");
      setBaseUrl("");
      setDefaultModel("");
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggleEnabled(config: AIProviderConfig) {
    setBusyId(config.id);
    setError(null);
    try {
      await api.ai.updateProvider(config.id, { is_enabled: !config.is_enabled });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleMakeDefault(config: AIProviderConfig) {
    setBusyId(config.id);
    setError(null);
    try {
      await api.ai.updateProvider(config.id, { is_default: true });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(config: AIProviderConfig) {
    setBusyId(config.id);
    setError(null);
    try {
      await api.ai.deleteProvider(config.id);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleModeChange(mode: OperatingMode) {
    if (!workspace) return;
    setError(null);
    try {
      const updated = await api.workspaces.update(workspace.id, { operating_mode: mode });
      setWorkspace(updated);
    } catch (err) {
      setError(String(err));
    }
  }

  async function handleSaveBudgets(e: React.FormEvent) {
    e.preventDefault();
    if (!workspace) return;
    setSavingBudget(true);
    setError(null);
    try {
      const updated = await api.workspaces.update(workspace.id, {
        monthly_budget_cents: monthlyBudget ? Math.round(parseFloat(monthlyBudget) * 100) : null,
        daily_budget_cents: dailyBudget ? Math.round(parseFloat(dailyBudget) * 100) : null,
      });
      setWorkspace(updated);
    } catch (err) {
      setError(String(err));
    } finally {
      setSavingBudget(false);
    }
  }

  const selectedProviderMeta = PROVIDERS.find((p) => p.value === provider)!;

  if (!user) {
    return (
      <div>
        <PageHeader
          title="AI Settings"
          description="Providers, operating mode, and usage for this workspace."
        />
        <EmptyState message="Sign in to configure AI providers." />
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="AI Settings"
        description="Bring your own provider keys, choose how JAIOS balances quality vs. cost, and see what's actually being used."
      />
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      <section className="mb-10">
        <h2 className="mb-2 text-sm font-medium">Operating mode</h2>
        <p className="mb-3 text-xs text-neutral-500">
          Drives which provider tier JAIOS reaches for by default — see each mode&rsquo;s
          description. You can still configure multiple providers regardless of mode.
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {OPERATING_MODES.map((mode) => {
            const active = workspace?.operating_mode === mode.value;
            return (
              <button
                key={mode.value}
                onClick={() => handleModeChange(mode.value)}
                className={`rounded-lg border p-3 text-left text-sm transition-colors ${
                  active
                    ? "border-neutral-900 bg-neutral-900 text-white dark:border-neutral-100 dark:bg-neutral-100 dark:text-neutral-900"
                    : "border-neutral-200 hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
                }`}
              >
                <div className="font-medium">{mode.label}</div>
                <div
                  className={`mt-1 text-xs ${active ? "opacity-80" : "text-neutral-500"}`}
                >
                  {mode.description}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-2 text-sm font-medium">Budgets</h2>
        <p className="mb-3 text-xs text-neutral-500">
          Soft caps only — usage above these is tracked and shown here, not blocked. Leave blank
          for no cap.
        </p>
        <form onSubmit={handleSaveBudgets} className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs text-neutral-500">Monthly budget</label>
            <input
              type="number"
              step="0.01"
              value={monthlyBudget}
              onChange={(e) => setMonthlyBudget(e.target.value)}
              placeholder="No cap"
              className="mt-1 w-36 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
            />
          </div>
          <div>
            <label className="block text-xs text-neutral-500">Daily budget</label>
            <input
              type="number"
              step="0.01"
              value={dailyBudget}
              onChange={(e) => setDailyBudget(e.target.value)}
              placeholder="No cap"
              className="mt-1 w-36 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
            />
          </div>
          <button
            type="submit"
            disabled={savingBudget}
            className="rounded-md border border-neutral-300 px-4 py-2 text-sm disabled:opacity-50 dark:border-neutral-700"
          >
            {savingBudget ? "Saving…" : "Save budgets"}
          </button>
        </form>
      </section>

      <section className="mb-10">
        <h2 className="mb-2 text-sm font-medium">Providers</h2>
        {providers.length === 0 ? (
          <EmptyState message="No providers configured yet — JAIOS is falling back to the server's default provider." />
        ) : (
          <div className="mb-4 space-y-2">
            {providers.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
              >
                <div>
                  <div className="flex items-center gap-2 font-medium">
                    {p.display_name || PROVIDERS.find((meta) => meta.value === p.provider)?.label}
                    {p.is_default && (
                      <span className="rounded-full bg-neutral-900 px-2 py-0.5 text-xs text-white dark:bg-neutral-100 dark:text-neutral-900">
                        default
                      </span>
                    )}
                    {!p.is_enabled && (
                      <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
                        disabled
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-neutral-500">
                    {p.provider}
                    {p.default_model ? ` · ${p.default_model}` : ""}
                    {p.base_url ? ` · ${p.base_url}` : ""}
                    {p.has_api_key ? " · key configured" : ""}
                  </div>
                </div>
                <div className="flex gap-2">
                  {!p.is_default && (
                    <button
                      onClick={() => handleMakeDefault(p)}
                      disabled={busyId === p.id}
                      className="rounded-md border border-neutral-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-neutral-700"
                    >
                      Make default
                    </button>
                  )}
                  <button
                    onClick={() => handleToggleEnabled(p)}
                    disabled={busyId === p.id}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-neutral-700"
                  >
                    {p.is_enabled ? "Disable" : "Enable"}
                  </button>
                  <button
                    onClick={() => handleDelete(p)}
                    disabled={busyId === p.id}
                    className="rounded-md border border-red-300 px-2 py-1 text-xs text-red-600 disabled:opacity-50 dark:border-red-900"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <form
          onSubmit={handleAddProvider}
          className="rounded-md border border-neutral-200 p-4 dark:border-neutral-800"
        >
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-neutral-500">
            Add a provider
          </h3>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-neutral-500">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as AIProviderKind)}
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
              >
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-neutral-500">
                Label <span className="text-neutral-400">(optional)</span>
              </label>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g. Production Claude key"
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
              />
            </div>
            {selectedProviderMeta.needsKey && (
              <div>
                <label className="block text-xs text-neutral-500">API key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-…"
                  className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
                />
              </div>
            )}
            {selectedProviderMeta.needsUrl && (
              <div>
                <label className="block text-xs text-neutral-500">Base URL</label>
                <input
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
                />
              </div>
            )}
            <div>
              <label className="block text-xs text-neutral-500">
                Default model <span className="text-neutral-400">(optional)</span>
              </label>
              <input
                value={defaultModel}
                onChange={(e) => setDefaultModel(e.target.value)}
                placeholder={provider === "ollama" ? "llama3.2:latest" : "claude-sonnet-5"}
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
            >
              {submitting ? "Adding…" : "Add provider"}
            </button>
          </div>
          <p className="mt-2 text-xs text-neutral-500">
            Keys are encrypted at rest and never shown again after saving — see the docs for the
            v1 encryption model and its limits.
          </p>
        </form>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-medium">Usage</h2>
        {!usage || usage.total_calls === 0 ? (
          <EmptyState message="No AI usage recorded yet for this workspace." />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Total calls" value={usage.total_calls} />
            <StatCard label="Tokens in" value={usage.total_tokens_in} />
            <StatCard label="Tokens out" value={usage.total_tokens_out} />
          </div>
        )}
        {usage && usage.total_calls > 0 && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Breakdown title="By provider" data={usage.calls_by_provider} />
            <Breakdown title="By task type" data={usage.calls_by_task_type} />
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
      <div className="text-sm text-neutral-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value.toLocaleString()}</div>
    </div>
  );
}

function Breakdown({ title, data }: { title: string; data: Record<string, number> }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-4 text-sm dark:border-neutral-800">
      <div className="mb-2 font-medium">{title}</div>
      <div className="space-y-1">
        {Object.entries(data).map(([key, count]) => (
          <div key={key} className="flex justify-between text-neutral-600 dark:text-neutral-400">
            <span>{key.replace(/_/g, " ")}</span>
            <span>{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
