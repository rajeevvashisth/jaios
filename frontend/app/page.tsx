"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type CeoSummary } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function OverviewPage() {
  const { activeCompanyId } = useCompany();
  const [summary, setSummary] = useState<CeoSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCompanyId) return;
    api.reports
      .ceoSummary(activeCompanyId)
      .then(setSummary)
      .catch((e) => setError(String(e)));
  }, [activeCompanyId]);

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Overview" description="Company-wide status at a glance." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Overview" description="Company-wide status at a glance." />
        <p className="text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (!summary) return <p className="text-sm text-neutral-500">Loading…</p>;

  return (
    <div>
      <PageHeader title="Overview" description="Company-wide status at a glance." />

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard label="Products" value={summary.portfolio.length} />
        <StatCard label="Open tasks" value={summary.operations.open_tasks} />
        <StatCard
          label="Active workflow runs"
          value={summary.operations.active_workflow_runs}
        />
        <StatCard label="Pending approvals" value={summary.operations.pending_approvals} />
      </div>

      <h2 className="mb-2 text-sm font-medium">Finance snapshot</h2>
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Revenue"
          valueText={formatMoney(summary.finance.revenue_cents, summary.finance.currency)}
        />
        <StatCard
          label="Expenses"
          valueText={formatMoney(summary.finance.expense_cents, summary.finance.currency)}
        />
        <StatCard
          label="Margin"
          valueText={formatMoney(summary.finance.margin_cents, summary.finance.currency)}
          highlight={summary.finance.margin_cents < 0 ? "negative" : "positive"}
        />
      </div>

      <div className="mb-8 grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <h2 className="mb-2 text-sm font-medium">Portfolio status</h2>
          {summary.portfolio.length === 0 ? (
            <EmptyState message="No products yet." />
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-neutral-500">
                <tr>
                  <th className="pb-2">Product</th>
                  <th className="pb-2">Stage</th>
                  <th className="pb-2">Open tasks</th>
                  <th className="pb-2">Projects</th>
                </tr>
              </thead>
              <tbody>
                {summary.portfolio.map((p) => (
                  <tr key={p.product_id} className="border-t border-neutral-200 dark:border-neutral-800">
                    <td className="py-2">
                      <Link href={`/products/${p.product_id}`} className="underline">
                        {p.name}
                      </Link>
                    </td>
                    <td className="py-2">{p.stage}</td>
                    <td className="py-2">
                      {p.task_counts.todo + p.task_counts.in_progress + p.task_counts.blocked}
                    </td>
                    <td className="py-2">{p.active_project_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div>
          <h2 className="mb-2 text-sm font-medium">Compliance</h2>
          {summary.compliance_overdue.length === 0 && summary.compliance_due_soon.length === 0 ? (
            <EmptyState message="Nothing overdue or due soon." />
          ) : (
            <div className="space-y-2">
              {[...summary.compliance_overdue, ...summary.compliance_due_soon].map((o) => (
                <div
                  key={o.id}
                  className="rounded-md border border-neutral-200 p-2 text-sm dark:border-neutral-800"
                >
                  <span className="font-medium">{o.title}</span>{" "}
                  <span className="text-xs text-neutral-500">
                    ({o.urgency.replace("_", " ")}, due {o.due_date})
                  </span>
                </div>
              ))}
              <Link href="/compliance" className="inline-block text-sm text-neutral-500 underline">
                Manage compliance →
              </Link>
            </div>
          )}
        </div>
      </div>

      <h2 className="mb-2 text-sm font-medium">Recent workflow runs</h2>
      {summary.recent_workflow_runs.length === 0 ? (
        <EmptyState message="No workflow runs yet." />
      ) : (
        <ul className="space-y-1 text-sm">
          {summary.recent_workflow_runs.map((run) => (
            <li key={run.id}>
              <Link href={`/workflows/${run.id}`} className="underline">
                {run.graph_name}
              </Link>{" "}
              <span className="text-xs text-neutral-500">— {run.status}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  valueText,
  highlight,
}: {
  label: string;
  value?: number;
  valueText?: string;
  highlight?: "positive" | "negative";
}) {
  return (
    <div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
      <div className="text-sm text-neutral-500">{label}</div>
      <div
        className={`mt-1 text-2xl font-semibold ${
          highlight === "negative"
            ? "text-red-600"
            : highlight === "positive"
              ? "text-green-600"
              : ""
        }`}
      >
        {valueText ?? value}
      </div>
    </div>
  );
}
