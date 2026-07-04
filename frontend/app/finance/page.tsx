"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type FinanceEntry, type FinanceSummary, type PaymentStatus, type Product } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Input, Label, Select } from "@/components/Field";

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
    api.products
      .list(activeCompanyId)
      .then(setProducts)
      .catch((e) => setError(String(e)));
    api.finance
      .summary(activeCompanyId, productId || undefined)
      .then(setSummary)
      .catch((e) => setError(String(e)));
    api.finance
      .listEntries(activeCompanyId, productId || undefined)
      .then(setEntries)
      .catch((e) => setError(String(e)));
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
    <div className="max-w-5xl">
      <PageHeader title="Finance" description="Revenue, cost, and margin visibility." />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div>
          <Label>Product</Label>
          <Select value={productId} onChange={(e) => setProductId(e.target.value)}>
            <option value="">Company-wide</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </div>
        <Button onClick={handleAskFinanceAgent} disabled={asking || !summary}>
          {asking ? "Asking…" : "Ask Finance Agent for a narrative"}
        </Button>
      </div>
      {startedRunId && (
        <p className="mb-4 text-sm" style={{ color: "var(--success)" }}>
          Started —{" "}
          <Link href={`/workflows/${startedRunId}`} className="underline">
            view trace
          </Link>
          .
        </p>
      )}
      {error && (
        <p className="mb-4 text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}

      {summary && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-4">
          <StatCard label="Revenue" value={formatMoney(summary.revenue_cents, summary.currency)} />
          <StatCard label="Expenses" value={formatMoney(summary.expense_cents, summary.currency)} />
          <StatCard
            label="Margin"
            value={formatMoney(summary.margin_cents, summary.currency)}
            tone={summary.margin_cents < 0 ? "danger" : "success"}
          />
          <StatCard
            label="Capital raised"
            value={formatMoney(summary.capital_cents, summary.currency)}
            hint="Equity, not income"
          />
        </div>
      )}

      <Card className="mb-6">
        <CardHeader title="Add an entry" />
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Type</Label>
            <Select
              value={entryType}
              onChange={(e) => setEntryType(e.target.value as "revenue" | "expense" | "capital")}
            >
              <option value="revenue">Revenue</option>
              <option value="expense">Expense</option>
              <option value="capital">Capital (founder/investor contribution)</option>
            </Select>
          </div>
          <div>
            <Label>Category</Label>
            <Input required value={category} onChange={(e) => setCategory(e.target.value)} placeholder="subscriptions" />
          </div>
          <div>
            <Label>Subcategory (optional)</Label>
            <Input value={subcategory} onChange={(e) => setSubcategory(e.target.value)} placeholder="hosting" />
          </div>
          <div>
            <Label>Amount</Label>
            <Input
              required
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="1000.00"
              className="w-32"
            />
          </div>
          <div>
            <Label>Date</Label>
            <Input required type="date" value={occurredOn} onChange={(e) => setOccurredOn(e.target.value)} />
          </div>
          <div className="min-w-[200px] flex-1">
            <Label>Description</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full"
            />
          </div>
          {entryType === "expense" && (
            <>
              <div>
                <Label>Vendor (optional)</Label>
                <Input value={vendor} onChange={(e) => setVendor(e.target.value)} />
              </div>
              <div>
                <Label>Payment status</Label>
                <Select value={paymentStatus} onChange={(e) => setPaymentStatus(e.target.value as PaymentStatus)}>
                  {PAYMENT_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, " ")}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label>Payment method (optional)</Label>
                <Input
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  placeholder="bank transfer"
                />
              </div>
              <div>
                <Label>Proof / invoice ref (optional)</Label>
                <Input
                  value={proofReference}
                  onChange={(e) => setProofReference(e.target.value)}
                  placeholder="invoice #, file link, etc."
                />
              </div>
            </>
          )}
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Adding…" : "Add entry"}
          </Button>
        </form>
      </Card>

      <CardHeader title="Ledger" />
      {entries.length === 0 ? (
        <EmptyState message="No finance entries yet." />
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => (
            <Card key={entry.id} className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 text-sm font-medium">
                  {entry.category}
                  {entry.subcategory && (
                    <span className="font-normal" style={{ color: "var(--text-tertiary)" }}>
                      · {entry.subcategory}
                    </span>
                  )}
                  <Badge tone={entry.entry_type === "expense" ? "warning" : entry.entry_type === "capital" ? "accent" : "success"}>
                    {entry.entry_type}
                  </Badge>
                  {entry.entry_type === "expense" && (
                    <Badge tone={entry.payment_status === "paid" ? "success" : "neutral"}>
                      {entry.payment_status.replace(/_/g, " ")}
                    </Badge>
                  )}
                </div>
                <div className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                  {entry.occurred_on}
                  {entry.vendor ? ` · ${entry.vendor}` : ""}
                  {entry.description ? ` · ${entry.description}` : ""}
                </div>
              </div>
              <div className="text-sm font-semibold">{formatMoney(entry.amount_cents, entry.currency)}</div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
  hint,
}: {
  label: string;
  value: string;
  tone?: "success" | "danger";
  hint?: string;
}) {
  return (
    <Card>
      <div className="text-sm" style={{ color: "var(--text-tertiary)" }}>
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold" style={tone ? { color: `var(--${tone})` } : undefined}>
        {value}
      </div>
      {hint && (
        <div className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
          {hint}
        </div>
      )}
    </Card>
  );
}
