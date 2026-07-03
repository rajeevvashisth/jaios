"use client";

import { useCompany } from "@/lib/company-context";

export function CompanySwitcher() {
  const { companies, activeCompanyId, setActiveCompanyId, loading } = useCompany();

  if (loading) return <div className="text-sm text-neutral-400">Loading…</div>;

  if (companies.length === 0) {
    return (
      <div className="text-sm text-neutral-500">
        No company yet — create one in Settings.
      </div>
    );
  }

  return (
    <select
      value={activeCompanyId ?? ""}
      onChange={(e) => setActiveCompanyId(e.target.value)}
      className="rounded-md border border-neutral-300 bg-transparent px-2 py-1 text-sm dark:border-neutral-700"
    >
      {companies.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name}
        </option>
      ))}
    </select>
  );
}
