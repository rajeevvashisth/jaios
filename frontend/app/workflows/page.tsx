"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type ApprovalRequest, type WorkflowRun } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function WorkflowsPage() {
  const { activeCompanyId } = useCompany();
  const { user } = useAuth();
  const [graphs, setGraphs] = useState<string[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [graphName, setGraphName] = useState("");
  const [goal, setGoal] = useState("");
  const [workspacePath, setWorkspacePath] = useState("");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decidingId, setDecidingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!activeCompanyId) return;
    const [r, a] = await Promise.all([
      api.workflows.list(activeCompanyId),
      api.workflows.pendingApprovals(activeCompanyId),
    ]);
    setRuns(r);
    setApprovals(a);
  }, [activeCompanyId]);

  useEffect(() => {
    api.workflows.graphs().then((g) => {
      setGraphs(g);
      setGraphName(g[0] ?? "");
    });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!activeCompanyId) return;
    setStarting(true);
    setError(null);
    try {
      await api.workflows.start({
        graph_name: graphName,
        company_id: activeCompanyId,
        goal,
        workspace_path: workspacePath || undefined,
      });
      setGoal("");
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setStarting(false);
    }
  }

  async function handleDecision(runId: string, approve: boolean) {
    setDecidingId(runId);
    setError(null);
    try {
      await api.workflows.decide(runId, { approve });
    } catch (err) {
      const message = String(err);
      // A 400 here almost always means someone (or another tab) already
      // decided this approval and the run moved on — the card is stale,
      // not a real failure, so just drop it via refresh rather than
      // surfacing a scary raw error.
      if (!message.includes("(400)")) {
        setError(message);
      }
    } finally {
      await refresh();
      setDecidingId(null);
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Workflows" description="Running and past workflow runs, plus approvals." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Workflows" description="Running and past workflow runs, plus approvals." />

      <form onSubmit={handleStart} className="mb-8 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-neutral-500">Graph</label>
          <select
            value={graphName}
            onChange={(e) => setGraphName(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {graphs.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[240px]">
          <label className="block text-xs text-neutral-500">Goal</label>
          <input
            required
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Ship v2 pricing page for Thandimandi"
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">
            Workspace path <span className="text-neutral-400">(optional)</span>
          </label>
          <input
            value={workspacePath}
            onChange={(e) => setWorkspacePath(e.target.value)}
            placeholder="defaults to server workspace"
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <button
          type="submit"
          disabled={starting || !graphName}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {starting ? "Starting…" : "Start workflow"}
        </button>
      </form>
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

      {approvals.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-2 text-sm font-medium">Pending approvals</h2>
          {!user && (
            <p className="mb-2 text-sm text-neutral-500">
              <Link href="/login" className="underline">
                Sign in
              </Link>{" "}
              as an admin or member to approve or reject these.
            </p>
          )}
          <div className="space-y-2">
            {approvals.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between rounded-md border border-amber-300 bg-amber-50 p-3 text-sm dark:border-amber-800 dark:bg-amber-950"
              >
                <div>
                  <div className="font-medium">{a.summary}</div>
                  <div className="text-xs text-neutral-500">
                    {a.action_type} · requested by {a.requested_by_agent_key}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDecision(a.workflow_run_id, true)}
                    disabled={!user || decidingId === a.workflow_run_id}
                    className="rounded-md bg-green-600 px-3 py-1 text-xs text-white disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleDecision(a.workflow_run_id, false)}
                    disabled={!user || decidingId === a.workflow_run_id}
                    className="rounded-md bg-red-600 px-3 py-1 text-xs text-white disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <h2 className="mb-2 text-sm font-medium">Runs</h2>
      {runs.length === 0 ? (
        <EmptyState message="No workflow runs yet." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-neutral-500">
            <tr>
              <th className="pb-2">Graph</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Started by</th>
              <th className="pb-2">Started at</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">
                  <Link href={`/workflows/${run.id}`} className="underline">
                    {run.graph_name}
                  </Link>
                </td>
                <td className="py-2">{run.status}</td>
                <td className="py-2">{run.initiating_actor}</td>
                <td className="py-2">{new Date(run.started_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
