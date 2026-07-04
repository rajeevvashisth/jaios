"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type ApplicabilityStatus,
  type ComplianceObligation,
  type FilingStatus,
} from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { Card } from "@/components/Card";
import { Badge, toneForUrgency } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Input, Label, Select } from "@/components/Field";

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
    api.compliance
      .listObligations(activeCompanyId, { includeCompleted })
      .then(setObligations)
      .catch((e) => setError(String(e)));
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
    setError(null);
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
    <div className="max-w-5xl">
      <PageHeader
        title="Compliance"
        description="Tax, legal, trademark, and contract obligations with reminders."
      />

      <Card className="mb-6">
        <Button onClick={handleSeedFramework} disabled={seeding}>
          {seeding ? "Seeding…" : "Seed standard India LLP compliance checklist"}
        </Button>
        <p className="mt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
          Adds the common MCA/ROC, income tax, GST, trademark, and local-registration categories as
          review-pending items — nothing is marked filed or given a fabricated due date.
        </p>
      </Card>

      <Card className="mb-6">
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3">
          <div className="min-w-[220px] flex-1">
            <Label>Title</Label>
            <Input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="File quarterly GST return"
              className="w-full"
            />
          </div>
          <div>
            <Label>Category</Label>
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Owner</Label>
            <Select value={ownerAgentKey} onChange={(e) => setOwnerAgentKey(e.target.value)}>
              {OWNERS.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Due date (optional)</Label>
            <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Adding…" : "Add obligation"}
          </Button>
        </form>
      </Card>

      <label
        className="mb-4 flex items-center gap-2 text-sm"
        style={{ color: "var(--text-secondary)" }}
      >
        <input
          type="checkbox"
          checked={includeCompleted}
          onChange={(e) => setIncludeCompleted(e.target.checked)}
        />
        Show completed
      </label>

      {error && (
        <p className="mb-4 text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}
      {startedRunId && (
        <p className="mb-4 text-sm" style={{ color: "var(--success)" }}>
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
            <Card key={o.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
                    {o.title}
                    <Badge tone={toneForUrgency(o.urgency)}>{o.urgency.replace(/_/g, " ")}</Badge>
                  </div>
                  <div className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                    {o.category}
                    {o.jurisdiction_level ? ` · ${o.jurisdiction_level.replace(/_/g, " ")}` : ""}
                    {o.governing_authority ? ` · ${o.governing_authority}` : ""}
                    {" · owner "}
                    {o.owner_agent_key ?? "—"}
                    {" · due "}
                    {o.due_date ?? "TBD"}
                    {o.external_owner ? ` · external: ${o.external_owner}` : ""}
                  </div>
                  {o.notes && (
                    <p className="mt-1 text-xs" style={{ color: "var(--text-tertiary)" }}>
                      {o.notes}
                    </p>
                  )}
                  {o.required_documents.length > 0 && (
                    <ul className="mt-1 text-xs" style={{ color: "var(--text-tertiary)" }}>
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
                    <Button size="sm" onClick={() => handleStartReview(o)} disabled={busyId === o.id}>
                      Start review
                    </Button>
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleComplete(o.id)}
                      disabled={busyId === o.id}
                    >
                      Mark complete
                    </Button>
                  </div>
                )}
              </div>

              <div
                className="mt-3 flex flex-wrap gap-4 pt-3"
                style={{ borderTop: "1px solid var(--border-subtle)" }}
              >
                <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                  Applicability
                  <Select
                    value={o.applicability_status}
                    disabled={busyId === o.id}
                    onChange={(e) =>
                      handleFieldUpdate(o.id, {
                        applicability_status: e.target.value as ApplicabilityStatus,
                      })
                    }
                    className="ml-2"
                  >
                    {APPLICABILITY_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, " ")}
                      </option>
                    ))}
                  </Select>
                </label>
                <label className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                  Filing status
                  <Select
                    value={o.filing_status}
                    disabled={busyId === o.id}
                    onChange={(e) =>
                      handleFieldUpdate(o.id, { filing_status: e.target.value as FilingStatus })
                    }
                    className="ml-2"
                  >
                    {FILING_STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, " ")}
                      </option>
                    ))}
                  </Select>
                </label>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
