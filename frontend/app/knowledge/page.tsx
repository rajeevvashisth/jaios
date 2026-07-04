"use client";

import { useState } from "react";
import { api, type KnowledgeSearchResult } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function KnowledgePage() {
  const { activeCompanyId } = useCompany();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setStatus("Ingesting…");
    try {
      await api.knowledge.ingest({
        company_id: activeCompanyId,
        title,
        source_type: "markdown",
        content,
      });
      setTitle("");
      setContent("");
      setStatus("Ingested.");
    } catch (err) {
      setStatus(String(err));
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setSearchError(null);
    try {
      const found = await api.knowledge.search({ company_id: activeCompanyId, query });
      setResults(found);
    } catch (err) {
      setSearchError(String(err));
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Knowledge" description="Company knowledge base — ingest and search." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Knowledge" description="Company knowledge base — ingest and search." />

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <form onSubmit={handleIngest} className="space-y-3">
          <h2 className="text-sm font-medium">Ingest a document</h2>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
          <textarea
            required
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste markdown / text content"
            rows={6}
            className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
          <button
            type="submit"
            className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white dark:bg-neutral-100 dark:text-neutral-900"
          >
            Ingest
          </button>
          {status && <p className="text-sm text-neutral-500">{status}</p>}
        </form>

        <form onSubmit={handleSearch} className="space-y-3">
          <h2 className="text-sm font-medium">Search</h2>
          <input
            required
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search company knowledge…"
            className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
          <button
            type="submit"
            className="rounded-md border border-neutral-300 px-4 py-2 text-sm dark:border-neutral-700"
          >
            Search
          </button>
          {searchError && <p className="text-sm text-red-500">{searchError}</p>}
          <div className="space-y-2">
            {results.map((r) => (
              <div
                key={`${r.document_id}-${r.chunk_index}`}
                className="rounded-md border border-neutral-200 p-3 text-sm dark:border-neutral-800"
              >
                <div className="text-xs text-neutral-500">
                  {r.document_title} · score {r.score.toFixed(2)}
                </div>
                <p className="mt-1">{r.content}</p>
              </div>
            ))}
          </div>
        </form>
      </div>
    </div>
  );
}
