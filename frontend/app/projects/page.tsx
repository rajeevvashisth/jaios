"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Product, type Project } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function ProjectsPage() {
  const { activeCompanyId } = useCompany();
  const [projects, setProjects] = useState<Project[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [productId, setProductId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.projects.list(activeCompanyId).then(setProjects);
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
      await api.projects.create({
        company_id: activeCompanyId,
        product_id: productId || undefined,
        name,
        goal: goal || undefined,
      });
      setName("");
      setGoal("");
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
        <PageHeader title="Projects" description="Projects grouped by product." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Projects" description="Projects grouped by product." />

      <form onSubmit={handleCreate} className="mb-8 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-neutral-500">Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Q3 growth push"
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Product</label>
          <select
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            <option value="">Company-level (no product)</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="min-w-[240px] flex-1">
          <label className="block text-xs text-neutral-500">Goal</label>
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Adding…" : "Add project"}
        </button>
      </form>
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      {projects.length === 0 ? (
        <EmptyState message="No projects yet." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-neutral-500">
            <tr>
              <th className="pb-2">Name</th>
              <th className="pb-2">Product</th>
              <th className="pb-2">Goal</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Target date</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.id} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">{project.name}</td>
                <td className="py-2">
                  {products.find((p) => p.id === project.product_id)?.name ?? "—"}
                </td>
                <td className="py-2">{project.goal ?? "—"}</td>
                <td className="py-2">{project.status}</td>
                <td className="py-2">{project.target_date ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
