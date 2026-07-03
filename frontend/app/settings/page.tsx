"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";

export default function SettingsPage() {
  const { companies, activeCompanyId, setActiveCompanyId, refreshCompanies } = useCompany();
  const [name, setName] = useState("");
  const [mission, setMission] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeCompany = companies.find((c) => c.id === activeCompanyId);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await api.companies.create({ name, mission: mission || undefined });
      await refreshCompanies();
      setActiveCompanyId(created.id);
      setName("");
      setMission("");
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl">
      <PageHeader title="Settings" description="Company profile and configuration." />

      {activeCompany && (
        <div className="mb-8 rounded-md border border-neutral-200 p-4 dark:border-neutral-800">
          <div className="text-sm text-neutral-500">Active company</div>
          <div className="mt-1 font-medium">{activeCompany.name}</div>
          {activeCompany.mission && (
            <div className="mt-1 text-sm text-neutral-500">{activeCompany.mission}</div>
          )}
        </div>
      )}

      <form onSubmit={handleCreate} className="space-y-4">
        <h2 className="text-sm font-medium">Create a company</h2>
        <div>
          <label className="block text-sm text-neutral-500">Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
            placeholder="Jyka Labs"
          />
        </div>
        <div>
          <label className="block text-sm text-neutral-500">Mission (optional)</label>
          <textarea
            value={mission}
            onChange={(e) => setMission(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
            rows={2}
          />
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Creating…" : "Create company"}
        </button>
      </form>
    </div>
  );
}
