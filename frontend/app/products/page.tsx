"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type Product } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const PRODUCT_TYPES = ["saas", "platform", "internal_tool", "ai_product", "other"];
const PRODUCT_STAGES = ["idea", "building", "live", "sunset"];

export default function ProductsPage() {
  const { activeCompanyId } = useCompany();
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState(PRODUCT_TYPES[0]);
  const [stage, setStage] = useState(PRODUCT_STAGES[0]);
  const [owner, setOwner] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.products.list(activeCompanyId).then(setProducts);
  }, [activeCompanyId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.products.create({
        company_id: activeCompanyId,
        name,
        type: type as Product["type"],
        stage: stage as Product["stage"],
        owner: owner || undefined,
        description: description || undefined,
      });
      setName("");
      setOwner("");
      setDescription("");
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader
          title="Products"
          description="The company's product portfolio — SaaS, platforms, internal tools, and more."
        />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Products"
        description="The company's product portfolio — SaaS, platforms, internal tools, and more."
      />

      <form onSubmit={handleCreate} className="mb-8 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-neutral-500">Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Thandimandi"
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {PRODUCT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Stage</label>
          <select
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {PRODUCT_STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Owner</label>
          <input
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div className="min-w-[240px] flex-1">
          <label className="block text-xs text-neutral-500">Description</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Adding…" : "Add product"}
        </button>
      </form>
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      {products.length === 0 ? (
        <EmptyState message="No products yet." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {products.map((product) => (
            <Link
              key={product.id}
              href={`/products/${product.id}`}
              className="block rounded-lg border border-neutral-200 p-4 hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
            >
              <div className="font-medium">{product.name}</div>
              <div className="mt-1 text-xs uppercase tracking-wide text-neutral-400">
                {product.type} · {product.stage}
              </div>
              {product.description && (
                <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
                  {product.description}
                </p>
              )}
              <div className="mt-2 text-xs text-neutral-500">Owner: {product.owner ?? "—"}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
