"use client";

import { useEffect, useState } from "react";
import { api, type AuditLogEntry } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function LogsPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.audit
      .list()
      .then(setEntries)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <PageHeader
        title="Logs / Traces"
        description="Append-only audit log of every agent decision and tool call."
      />
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
      {entries.length === 0 ? (
        <EmptyState message="No audit log entries yet." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-neutral-500">
            <tr>
              <th className="pb-2">Time</th>
              <th className="pb-2">Actor</th>
              <th className="pb-2">Action</th>
              <th className="pb-2">Tool</th>
              <th className="pb-2">Target</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">{new Date(entry.occurred_at).toLocaleString()}</td>
                <td className="py-2">
                  {entry.actor_type}:{entry.actor_key}
                </td>
                <td className="py-2">{entry.action}</td>
                <td className="py-2">{entry.tool_used ?? "—"}</td>
                <td className="py-2">
                  {entry.target_type ? `${entry.target_type}:${entry.target_id}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
