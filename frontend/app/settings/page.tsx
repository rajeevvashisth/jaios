"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";

const ENTITY_TYPES = ["LLP", "Pvt Ltd", "Sole Proprietorship", "Partnership", "Other"];

export default function SettingsPage() {
  const { companies, activeCompanyId, setActiveCompanyId, refreshCompanies } = useCompany();
  const [name, setName] = useState("");
  const [mission, setMission] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeCompany = companies.find((c) => c.id === activeCompanyId);

  const [entityType, setEntityType] = useState("");
  const [country, setCountry] = useState("India");
  const [jurisdictionState, setJurisdictionState] = useState("");
  const [baseCurrency, setBaseCurrency] = useState("INR");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);

  useEffect(() => {
    if (!activeCompany) return;
    setEntityType(activeCompany.entity_type ?? "");
    setCountry(activeCompany.country);
    setJurisdictionState(activeCompany.jurisdiction_state ?? "");
    setBaseCurrency(activeCompany.base_currency);
  }, [activeCompany]);

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

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setSavingProfile(true);
    setProfileError(null);
    setProfileSaved(false);
    try {
      await api.companies.update(activeCompanyId, {
        entity_type: entityType || null,
        country,
        jurisdiction_state: jurisdictionState || null,
        base_currency: baseCurrency,
      });
      await refreshCompanies();
      setProfileSaved(true);
    } catch (err) {
      setProfileError(String(err));
    } finally {
      setSavingProfile(false);
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

      {activeCompany && (
        <form onSubmit={handleSaveProfile} className="mb-8 space-y-4">
          <h2 className="text-sm font-medium">Legal / jurisdiction profile</h2>
          <p className="text-xs text-neutral-500">
            Drives which compliance framework applies (see Compliance page) and how finance is
            denominated. Leave a field blank if unknown rather than guessing.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-neutral-500">Entity type</label>
              <select
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
              >
                <option value="">Unset</option>
                {ENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-neutral-500">Country</label>
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-500">Jurisdiction state</label>
              <input
                value={jurisdictionState}
                onChange={(e) => setJurisdictionState(e.target.value)}
                placeholder="Delhi"
                className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-500">Base currency</label>
              <input
                value={baseCurrency}
                onChange={(e) => setBaseCurrency(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
              />
            </div>
          </div>
          {profileError && <p className="text-sm text-red-500">{profileError}</p>}
          {profileSaved && <p className="text-sm text-green-600">Saved.</p>}
          <button
            type="submit"
            disabled={savingProfile}
            className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {savingProfile ? "Saving…" : "Save profile"}
          </button>
        </form>
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
