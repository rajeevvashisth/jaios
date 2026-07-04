"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type FinanceEntry, type FinanceSummary, type PaymentStatus, type Product } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const PAYMENT_STATUSES: PaymentStatus[] = ["paid", "unpaid", "partially_paid", "reimbursable"];

export default function FinancePage() {
  const { activeCompanyId } = useCompany();
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState("");
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [entries, setEntries] = useState<FinanceEntry[]>([]);

  const [entryType, setEntryType] = useState<"revenue" | "expense" | "capital">("revenue");
  const [category, setCategory] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [amount, setAmount] = useState("");
  const [occurredOn, setOccurredOn] = useState("");
  const [description, setDescription] = useState("");
  const [vendor, setVendor] = useState("");
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>("paid");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [proofReference, setProofReference] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [asking, setAsking] = useState(false);
  const [startedRunId, setStartedRunId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.products.list(activeCompanyId).then(setProducts);
    api.finance.summary(activeCompanyId, productId || undefined).then(setSummary);
    api.finance.listEntries(activeCompanyId, productId || undefined).then(setEntries);
  }, [activeCompanyId, productId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setSubmitting(true);
    setError(null);
    try {
      const cents = Math.round(parseFloat(amount) * 100);
      await api.finance.createEntry({
        company_id: activeCompanyId,
        product_id: productId || undefined,
        entry_type: entryType,
        category,
        subcategory: subcategory || undefined,
        amount_cents: cents,
        occurred_on: occurredOn,
        description: description || undefined,
        vendor: vendor || undefined,
        payment_status: paymentStatus,
        payment_method: paymentMethod || undefined,
        proof_reference: proofReference ? { reference: proofReference } : undefined,
      });
      setCategory("");
      setSubcategory("");
      setAmount("");
      setDescription("");
      setVendor("");
      setPaymentMethod("");
      setProofReference("");
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAskFinanceAgent() {
    if (!activeCompanyId || !summary) return;
    setAsking(true);
    setError(null);
    try {
      const goal =
        `Review company financials. Revenue: ${formatMoney(summary.revenue_cents, summary.currency)}, ` +
        `Expenses: ${formatMoney(summary.expense_cents, summary.currency)}, ` +
        `Margin: ${formatMoney(summary.margin_cents, summary.currency)}. ` +
        `Revenue by category: ${summary.revenue_by_category.map((c) => `${c.category}=${formatMoney(c.amount_cents, summary.currency)}`).join(", ") || "none"}. ` +
        `Expense by category: ${summary.expense_by_category.map((c) => `${c.category}=${formatMoney(c.amount_cents, summary.currency)}`).join(", ") || "none"}. ` +
        `Recommend where to focus.`;
      const run = await api.workflows.start({
        graph_name: "revenue_cost_review",
        company_id: activeCompanyId,
        goal,
      });
      setStartedRunId(run.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setAsking(false);
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Finance" description="Revenue, cost, and margin visibility." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Finance" description="Revenue, cost, and margin visibility." />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-neutral-500">Product</label>
          <select
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            <option value="">Company-wide</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleAskFinanceAgent}
          disabled={asking || !summary}
          className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-neutral-700"
        >
          {asking ? "Asking…" : "Ask Finance Agent for a narrative"}
        </button>
      </div>
      {startedRunId && (
        <p className="mb-4 text-sm text-green-600">
          Started —{" "}
          <Link href={`/workflows/${startedRunId}`} className="underline">
            view trace
          </Link>
          .
        </p>
      )}
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      {summary && (
        <>
          <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Revenue" value={formatMoney(summary.revenue_cents, summary.currency)} />
            <StatCard label="Expenses" value={formatMoney(summary.expense_cents, summary.currency)} />
            <StatCard
              label="Margin"
              value={formatMoney(summary.margin_cents, summary.currency)}
              highlight={summary.margin_cents < 0 ? "negative" : "positive"}
            />
          </div>
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label="Capital raised (equity, not income)"
              value={formatMoney(summary.capital_cents, summary.currency)}
            />
          </div>
        </>
      )}

      <form onSubmit={handleCreate} className="mb-8 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-neutral-500">Type</label>
          <select
            value={entryType}
            onChange={(e) => setEntryType(e.target.value as "revenue" | "expense" | "capital")}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            <option value="revenue">Revenue</option>
            <option value="expense">Expense</option>
            <option value="capital">Capital (founder/investor contribution)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Category</label>
          <input
            required
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="subscriptions"
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">
            Subcategory <span className="text-neutral-400">(optional)</span>
          </label>
          <input
            value={subcategory}
            onChange={(e) => setSubcategory(e.target.value)}
            placeholder="hosting"
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Amount</label>
          <input
            required
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="1000.00"
            className="mt-1 w-32 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Date</label>
          <input
            required
            type="date"
            value={occurredOn}
            onChange={(e) => setOccurredOn(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div className="min-w-[200px] flex-1">
          <label className="block text-xs text-neutral-500">Description</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        {entryType === "expense" && (
          <>
            <div>
              <label className="block text-xs text-neutral-500">
                Vendor <span className="text-neutral-400">(optional)</span>
              </label>
              <input
                value={vendor}
                onChange={(e) => setVendor(e.target.value)}
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500">Payment status</label>
              <select
                value={paymentStatus}
                onChange={(e) => setPaymentStatus(e.target.value as PaymentStatus)}
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
              >
                {PAYMENT_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-neutral-500">
                Payment method <span className="text-neutral-400">(optional)</span>
              </label>
              <input
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                placeholder="bank transfer"
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500">
                Proof / invoice ref <span className="text-neutral-400">(optional)</span>
              </label>
              <input
                value={proofReference}
                onChange={(e) => setProofReference(e.target.value)}
                placeholder="invoice #, file link, etc."
                className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
              />
            </div>
          </>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Adding…" : "Add entry"}
        </button>
      </form>

      {entries.length === 0 ? (
        <EmptyState message="No finance entries yet." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-neutral-500">
            <tr>
              <th className="pb-2">Date</th>
              <th className="pb-2">Type</th>
              <th className="pb-2">Category</th>
              <th className="pb-2">Amount</th>
              <th className="pb-2">Vendor</th>
              <th className="pb-2">Payment</th>
              <th className="pb-2">Description</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">{entry.occurred_on}</td>
                <td className="py-2">
                  {entry.entry_type}
                  {entry.subcategory ? ` · ${entry.subcategory}` : ""}
                </td>
                <td className="py-2">{entry.category}</td>
                <td className="py-2">{formatMoney(entry.amount_cents, entry.currency)}</td>
                <td className="py-2">{entry.vendor ?? "—"}</td>
                <td className="py-2 text-xs">
                  {entry.entry_type === "expense" ? entry.payment_status.replace(/_/g, " ") : "—"}
                </td>
                <td className="py-2">{entry.description ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
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
        {value}
      </div>
    </div>
  );
}
