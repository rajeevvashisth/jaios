"use client";

import { useState } from "react";
import { api, type MemoryRecord } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function MemoryPage() {
  const { activeCompanyId } = useCompany();
  const [records, setRecords] = useState<MemoryRecord[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCompanyMemory() {
    if (!activeCompanyId) return;
    setError(null);
    try {
      const results = await api.memory.list("company", activeCompanyId);
      setRecords(results);
      setLoaded(true);
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <div>
      <PageHeader
        title="Memory / Activity"
        description="Structured memory records, browsable by scope."
      />
      {!activeCompanyId ? (
        <EmptyState message="Create a company in Settings to get started." />
      ) : (
        <>
          <button
            onClick={loadCompanyMemory}
            className="mb-4 rounded-md border border-neutral-300 px-3 py-1.5 text-sm dark:border-neutral-700"
          >
            Load company-scope memory
          </button>
          {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
          {loaded && records.length === 0 && <EmptyState message="No memory records yet." />}
          <div className="space-y-2">
            {records.map((r) => (
              <div
                key={r.id}
                className="rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
              >
                <div className="flex justify-between text-xs text-neutral-500">
                  <span>
                    {r.kind} · {r.agent_key ?? "unscoped"}
                  </span>
                  <span>{new Date(r.created_at).toLocaleString()}</span>
                </div>
                <pre className="mt-1 whitespace-pre-wrap break-words text-xs">
                  {JSON.stringify(r.content, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
