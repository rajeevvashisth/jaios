"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Product, type ProductStatusReport } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { PageHeader } from "@/components/PageHeader";
import { LoadingState } from "@/components/Spinner";

export default function ProductStatusPage() {
  const params = useParams<{ productId: string }>();
  const [report, setReport] = useState<ProductStatusReport | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [workspacePath, setWorkspacePath] = useState("");
  const [savingWorkspace, setSavingWorkspace] = useState(false);
  const [workspaceSaved, setWorkspaceSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports
      .productStatus(params.productId)
      .then(setReport)
      .catch((e) => setError(String(e)));
    api.products
      .get(params.productId)
      .then((p) => {
        setProduct(p);
        setWorkspacePath(p.local_workspace_path ?? "");
      })
      .catch((e) => setError(String(e)));
  }, [params.productId]);

  async function handleSaveWorkspace(e: React.FormEvent) {
    e.preventDefault();
    setSavingWorkspace(true);
    setWorkspaceSaved(false);
    setError(null);
    try {
      const updated = await api.products.update(params.productId, {
        local_workspace_path: workspacePath || null,
      });
      setProduct(updated);
      setWorkspaceSaved(true);
    } catch (err) {
      setError(String(err));
    } finally {
      setSavingWorkspace(false);
    }
  }

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

  if (!report) return <LoadingState />;

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

      <h2 className="mb-2 text-sm font-medium">Workspace</h2>
      {product && (
        <form
          onSubmit={handleSaveWorkspace}
          className="mb-8 flex flex-wrap items-end gap-3 rounded-md border border-neutral-200 p-4 dark:border-neutral-800"
        >
          <div className="min-w-[320px] flex-1">
            <label className="block text-xs text-neutral-500">Local workspace path</label>
            <input
              value={workspacePath}
              onChange={(e) => setWorkspacePath(e.target.value)}
              placeholder="/Users/you/Documents/Apps/YourProduct"
              className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
            />
            <p className="mt-1 text-xs text-neutral-500">
              Workflows started for this product (or its tasks/projects) default to this path
              unless a workspace is passed explicitly.
            </p>
          </div>
          <button
            type="submit"
            disabled={savingWorkspace}
            className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {savingWorkspace ? "Saving…" : "Save"}
          </button>
          {workspaceSaved && <p className="text-sm text-green-600">Saved.</p>}
        </form>
      )}

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
