"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type ApplicabilityStatus,
  type ComplianceObligation,
  type ComplianceUrgency,
  type FilingStatus,
} from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const CATEGORIES = ["tax", "legal", "trademark", "contract", "corporate", "other"];
const OWNERS = ["finance", "legal", "operations"];

const APPLICABILITY_OPTIONS: ApplicabilityStatus[] = ["review_pending", "applicable", "not_applicable"];

const FILING_STATUS_OPTIONS: FilingStatus[] = [
  "draft",
  "under_review",
  "not_applicable",
  "applicability_review_pending",
  "upcoming",
  "in_progress",
  "awaiting_documents",
  "awaiting_finance_input",
  "awaiting_ca_vendor",
  "ready_for_filing",
  "filed",
  "filed_proof_pending",
  "completed",
  "overdue",
];

const URGENCY_STYLES: Record<ComplianceUrgency, string> = {
  overdue: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  due_soon: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  upcoming: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
  completed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  review_pending: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
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
  const [seeding, setSeeding] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startedRunId, setStartedRunId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.compliance.listObligations(activeCompanyId, { includeCompleted }).then(setObligations);
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
        due_date: dueDate || undefined,
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

  async function handleSeedFramework() {
    if (!activeCompanyId) return;
    setSeeding(true);
    setError(null);
    try {
      await api.compliance.seedIndiaLlpFramework(activeCompanyId);
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSeeding(false);
    }
  }

  async function handleFieldUpdate(
    id: string,
    payload: Parameters<typeof api.compliance.update>[1],
  ) {
    setBusyId(id);
    setError(null);
    try {
      await api.compliance.update(id, payload);
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyId(null);
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
        goal: `Review compliance obligation: ${obligation.title} (due ${obligation.due_date ?? "date TBD"}).`,
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

      <div className="mb-6">
        <button
          onClick={handleSeedFramework}
          disabled={seeding}
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-neutral-700"
        >
          {seeding ? "Seeding…" : "Seed standard India LLP compliance checklist"}
        </button>
        <p className="mt-1 text-xs text-neutral-500">
          Adds the common MCA/ROC, income tax, GST, trademark, and local-registration categories as
          review-pending items — nothing is marked filed or given a fabricated due date.
        </p>
      </div>

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
          <label className="block text-xs text-neutral-500">
            Due date <span className="text-neutral-400">(optional)</span>
          </label>
          <input
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
              className="rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2 font-medium">
                    {o.title}
                    <span className={`rounded-full px-2 py-0.5 text-xs ${URGENCY_STYLES[o.urgency]}`}>
                      {o.urgency.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs text-neutral-500">
                    {o.category}
                    {o.jurisdiction_level ? ` · ${o.jurisdiction_level.replace(/_/g, " ")}` : ""}
                    {o.governing_authority ? ` · ${o.governing_authority}` : ""}
                    {" · owner "}
                    {o.owner_agent_key ?? "—"}
                    {" · due "}
                    {o.due_date ?? "TBD"}
                    {o.external_owner ? ` · external: ${o.external_owner}` : ""}
                  </div>
                  {o.notes && <p className="mt-1 text-xs text-neutral-500">{o.notes}</p>}
                  {o.required_documents.length > 0 && (
                    <ul className="mt-1 text-xs text-neutral-500">
                      {o.required_documents.map((doc) => (
                        <li key={doc.name}>
                          {doc.obtained ? "✓" : "○"} {doc.name}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                {!o.completed && (
                  <div className="flex shrink-0 gap-2">
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

              <div className="mt-2 flex flex-wrap gap-3 border-t border-neutral-100 pt-2 dark:border-neutral-800">
                <label className="text-xs text-neutral-500">
                  Applicability
                  <select
                    value={o.applicability_status}
                    disabled={busyId === o.id}
                    onChange={(e) =>
                      handleFieldUpdate(o.id, {
                        applicability_status: e.target.value as ApplicabilityStatus,
                      })
                    }
                    className="ml-2 rounded-md border border-neutral-300 bg-transparent px-1.5 py-1 text-xs dark:border-neutral-700"
                  >
                    {APPLICABILITY_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-neutral-500">
                  Filing status
                  <select
                    value={o.filing_status}
                    disabled={busyId === o.id}
                    onChange={(e) =>
                      handleFieldUpdate(o.id, { filing_status: e.target.value as FilingStatus })
                    }
                    className="ml-2 rounded-md border border-neutral-300 bg-transparent px-1.5 py-1 text-xs dark:border-neutral-700"
                  >
                    {FILING_STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
