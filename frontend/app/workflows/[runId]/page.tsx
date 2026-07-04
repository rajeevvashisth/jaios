"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type ApprovalRequest, type WorkflowRun, type WorkflowStep } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

export default function WorkflowRunDetailPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const { user } = useAuth();

  const [run, setRun] = useState<WorkflowRun | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deciding, setDeciding] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [runData, stepData, approvals] = await Promise.all([
        api.workflows.get(runId),
        api.workflows.steps(runId),
        api.workflows.pendingApprovals(),
      ]);
      setRun(runData);
      setSteps(stepData);
      setPendingApproval(approvals.find((a) => a.workflow_run_id === runId) ?? null);
    } catch (err) {
      setError(String(err));
    }
  }, [runId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleDecision(approve: boolean) {
    setDeciding(true);
    try {
      await api.workflows.decide(runId, { approve });
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setDeciding(false);
    }
  }

  if (error) {
    return (
      <div>
        <Link href="/workflows" className="text-sm text-neutral-500 underline">
          ← Workflows
        </Link>
        <p className="mt-4 text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (!run) return <p className="text-sm text-neutral-500">Loading…</p>;

  return (
    <div>
      <Link href="/workflows" className="text-sm text-neutral-500 underline">
        ← Workflows
      </Link>
      <PageHeader
        title={`${run.graph_name} — ${run.status}`}
        description={`Started by ${run.initiating_actor} at ${new Date(run.started_at).toLocaleString()}`}
      />

      {pendingApproval && (
        <div className="mb-8 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm dark:border-amber-800 dark:bg-amber-950">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{pendingApproval.summary}</div>
              <div className="text-xs text-neutral-500">
                {pendingApproval.action_type} · requested by{" "}
                {pendingApproval.requested_by_agent_key}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleDecision(true)}
                disabled={!user || deciding}
                className="rounded-md bg-green-600 px-3 py-1 text-xs text-white disabled:opacity-50"
              >
                Approve
              </button>
              <button
                onClick={() => handleDecision(false)}
                disabled={!user || deciding}
                className="rounded-md bg-red-600 px-3 py-1 text-xs text-white disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          </div>
          {!user && (
            <p className="mt-2 text-sm text-neutral-500">
              <Link href="/login" className="underline">
                Sign in
              </Link>{" "}
              as an admin or member to approve or reject this.
            </p>
          )}
        </div>
      )}

      <h2 className="mb-2 text-sm font-medium">Step trace</h2>
      {steps.length === 0 ? (
        <EmptyState message="No steps recorded yet." />
      ) : (
        <ol className="space-y-3 border-l border-neutral-200 pl-4 dark:border-neutral-800">
          {steps.map((step) => (
            <li key={step.id} className="relative">
              <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-neutral-400" />
              <div className="flex items-center justify-between">
                <span className="font-medium">{step.agent_key}</span>
                <span className="text-xs text-neutral-500">{step.status}</span>
              </div>
              <div className="text-xs text-neutral-400">
                {new Date(step.started_at).toLocaleTimeString()}
                {step.completed_at && ` → ${new Date(step.completed_at).toLocaleTimeString()}`}
              </div>
              {typeof step.output?.response === "string" && (
                <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-600 dark:text-neutral-400">
                  {step.output.response}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
