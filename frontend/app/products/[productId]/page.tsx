"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type ProductStatusReport } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { PageHeader } from "@/components/PageHeader";

export default function ProductStatusPage() {
  const params = useParams<{ productId: string }>();
  const [report, setReport] = useState<ProductStatusReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports
      .productStatus(params.productId)
      .then(setReport)
      .catch((e) => setError(String(e)));
  }, [params.productId]);

  if (error) {
    return (
      <div>
        <Link href="/products" className="text-sm text-neutral-500 underline">
          ← Products
        </Link>
        <p className="mt-4 text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (!report) return <p className="text-sm text-neutral-500">Loading…</p>;

  return (
    <div>
      <Link href="/products" className="text-sm text-neutral-500 underline">
        ← Products
      </Link>
      <PageHeader
        title={report.name}
        description={`${report.stage} · ${report.status} · ${report.project_count} project(s)`}
      />

      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard label="Todo" value={report.task_counts.todo} />
        <StatCard label="In progress" value={report.task_counts.in_progress} />
        <StatCard label="Blocked" value={report.task_counts.blocked} />
        <StatCard label="Done" value={report.task_counts.done} />
      </div>

      <h2 className="mb-2 text-sm font-medium">Finance</h2>
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Revenue"
          valueText={formatMoney(report.finance.revenue_cents, report.finance.currency)}
        />
        <StatCard
          label="Expenses"
          valueText={formatMoney(report.finance.expense_cents, report.finance.currency)}
        />
        <StatCard
          label="Margin"
          valueText={formatMoney(report.finance.margin_cents, report.finance.currency)}
        />
      </div>

      <h2 className="mb-2 text-sm font-medium">Compliance obligations</h2>
      {report.compliance_obligations.length === 0 ? (
        <p className="text-sm text-neutral-500">None open for this product.</p>
      ) : (
        <div className="space-y-2">
          {report.compliance_obligations.map((o) => (
            <div
              key={o.id}
              className="rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
            >
              <div className="font-medium">{o.title}</div>
              <div className="text-xs text-neutral-500">
                {o.category} · due {o.due_date} · {o.urgency.replace("_", " ")}
              </div>
            </div>
          ))}
        </div>
      )}
      <Link href="/compliance" className="mt-2 inline-block text-sm text-neutral-500 underline">
        Manage compliance →
      </Link>
    </div>
  );
}

function StatCard({
  label,
  value,
  valueText,
}: {
  label: string;
  value?: number;
  valueText?: string;
}) {
  return (
    <div className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
      <div className="text-sm text-neutral-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{valueText ?? value}</div>
    </div>
  );
}
