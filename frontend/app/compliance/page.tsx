"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type ComplianceObligation, type ComplianceUrgency } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const CATEGORIES = ["tax", "legal", "trademark", "contract", "other"];
const OWNERS = ["finance", "legal", "operations"];

const URGENCY_STYLES: Record<ComplianceUrgency, string> = {
  overdue: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  due_soon: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  upcoming: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
  completed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
};

export default function CompliancePage() {
  const { activeCompanyId } = useCompany();
  const [obligations, setObligations] = useState<ComplianceObligation[]>([]);
  const [includeCompleted, setIncludeCompleted] = useState(false);

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [ownerAgentKey, setOwnerAgentKey] = useState(OWNERS[0]);
  const [dueDate, setDueDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startedRunId, setStartedRunId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.compliance
      .listObligations(activeCompanyId, { includeCompleted })
      .then(setObligations);
  }, [activeCompanyId, includeCompleted]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.compliance.create({
        company_id: activeCompanyId,
        title,
        category,
        owner_agent_key: ownerAgentKey,
        due_date: dueDate,
      });
      setTitle("");
      setDueDate("");
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleComplete(id: string) {
    setBusyId(id);
    try {
      await api.compliance.complete(id);
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function handleStartReview(obligation: ComplianceObligation) {
    if (!activeCompanyId) return;
    setBusyId(obligation.id);
    setError(null);
    try {
      const run = await api.workflows.start({
        graph_name: "compliance_review",
        company_id: activeCompanyId,
        goal: `Review compliance obligation: ${obligation.title} (due ${obligation.due_date}).`,
      });
      setStartedRunId(run.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader
          title="Compliance"
          description="Tax, legal, trademark, and contract obligations with reminders."
        />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Compliance"
        description="Tax, legal, trademark, and contract obligations with reminders."
      />

      <form onSubmit={handleCreate} className="mb-6 flex flex-wrap items-end gap-3">
        <div className="min-w-[220px] flex-1">
          <label className="block text-xs text-neutral-500">Title</label>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="File quarterly GST return"
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Owner</label>
          <select
            value={ownerAgentKey}
            onChange={(e) => setOwnerAgentKey(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {OWNERS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Due date</label>
          <input
            required
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Adding…" : "Add obligation"}
        </button>
      </form>

      <label className="mb-4 flex items-center gap-2 text-sm text-neutral-500">
        <input
          type="checkbox"
          checked={includeCompleted}
          onChange={(e) => setIncludeCompleted(e.target.checked)}
        />
        Show completed
      </label>

      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
      {startedRunId && (
        <p className="mb-4 text-sm text-green-600">
          Started —{" "}
          <Link href={`/workflows/${startedRunId}`} className="underline">
            view trace
          </Link>
          .
        </p>
      )}

      {obligations.length === 0 ? (
        <EmptyState message="No compliance obligations yet." />
      ) : (
        <div className="space-y-2">
          {obligations.map((o) => (
            <div
              key={o.id}
              className="flex items-center justify-between rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
            >
              <div>
                <div className="flex items-center gap-2 font-medium">
                  {o.title}
                  <span className={`rounded-full px-2 py-0.5 text-xs ${URGENCY_STYLES[o.urgency]}`}>
                    {o.urgency.replace("_", " ")}
                  </span>
                </div>
                <div className="text-xs text-neutral-500">
                  {o.category} · owner {o.owner_agent_key ?? "—"} · due {o.due_date}
                </div>
              </div>
              {!o.completed && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleStartReview(o)}
                    disabled={busyId === o.id}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-neutral-700"
                  >
                    Start review
                  </button>
                  <button
                    onClick={() => handleComplete(o.id)}
                    disabled={busyId === o.id}
                    className="rounded-md bg-green-600 px-2 py-1 text-xs text-white disabled:opacity-50"
                  >
                    Mark complete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
