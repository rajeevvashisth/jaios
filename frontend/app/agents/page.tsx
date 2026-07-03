"use client";

import { useEffect, useState } from "react";
import { api, type AgentSpec } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentSpec[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.agents.list().then(setAgents).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <PageHeader
        title="Agents"
        description="The 8 core agents, their tool permissions, and delegation rules."
      />
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
      {agents.length === 0 ? (
        <EmptyState message="No agents found — is the backend running?" />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {agents.map((agent) => (
            <div
              key={agent.key}
              className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
            >
              <div className="flex items-center justify-between">
                <div className="font-medium">{agent.name}</div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    agent.enabled
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800"
                  }`}
                >
                  {agent.enabled ? "enabled" : "disabled"}
                </span>
              </div>
              <div className="mt-1 text-xs uppercase tracking-wide text-neutral-400">
                {agent.layer}
              </div>
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                {agent.responsibility}
              </p>
              <dl className="mt-3 space-y-1 text-xs text-neutral-500">
                <div>
                  <dt className="inline font-medium">Tools: </dt>
                  <dd className="inline">{agent.allowed_tools.join(", ") || "none"}</dd>
                </div>
                <div>
                  <dt className="inline font-medium">Delegates to: </dt>
                  <dd className="inline">{agent.can_delegate_to.join(", ") || "none"}</dd>
                </div>
                <div>
                  <dt className="inline font-medium">Requires approval for: </dt>
                  <dd className="inline">{agent.requires_approval_for.join(", ") || "none"}</dd>
                </div>
                {agent.escalates_to && (
                  <div>
                    <dt className="inline font-medium">Escalates to: </dt>
                    <dd className="inline">{agent.escalates_to}</dd>
                  </div>
                )}
              </dl>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
