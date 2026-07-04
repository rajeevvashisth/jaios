"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type AIUsageSummary, type CeoSummary } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { useCompany } from "@/lib/company-context";
import { useAuth } from "@/lib/auth-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { LoadingState } from "@/components/Spinner";

export default function CommandCenterPage() {
  const { activeCompanyId, companies } = useCompany();
  const { user } = useAuth();
  const [summary, setSummary] = useState<CeoSummary | null>(null);
  const [usage, setUsage] = useState<AIUsageSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeCompanyId) return;
    api.reports
      .ceoSummary(activeCompanyId)
      .then(setSummary)
      .catch((e) => setError(String(e)));
  }, [activeCompanyId]);

  useEffect(() => {
    if (!user) return;
    api.workspaces
      .getMine()
      .then((ws) => api.ai.usageSummary(ws.id))
      .then(setUsage)
      .catch(() => {
        // Usage visibility is a nice-to-have on this page, not load-bearing
        // — a missing workspace/usage endpoint shouldn't blank the page.
      });
  }, [user]);

  const activeCompany = companies.find((c) => c.id === activeCompanyId);

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Command Center" description="Company-wide status at a glance." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Command Center" description="Company-wide status at a glance." />
        <p className="text-sm" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      </div>
    );
  }

  if (!summary) return <LoadingState />;

  const attentionItems = buildAttentionItems(summary);

  return (
    <div className="max-w-6xl">
      <PageHeader
        title={`Good to see you${activeCompany ? ` — ${activeCompany.name}` : ""}`}
        description="Here's what's moving, what's blocked, and what needs a decision."
      />

      <QuickActions />

      <div className="mb-6">
        <CardHeader
          title="Needs attention"
          description={
            attentionItems.length === 0
              ? undefined
              : `${attentionItems.length} item${attentionItems.length === 1 ? "" : "s"} worth a look`
          }
        />
        {attentionItems.length === 0 ? (
          <Card>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              All clear — nothing overdue, blocked, or waiting on your approval.
            </p>
          </Card>
        ) : (
          <div className="space-y-2">
            {attentionItems.map((item) => (
              <Card key={item.key} className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 text-sm font-medium">
                    {item.title}
                    <Badge tone={item.tone}>{item.badge}</Badge>
                  </div>
                  {item.detail && (
                    <div className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                      {item.detail}
                    </div>
                  )}
                </div>
                <Link
                  href={item.href}
                  className="text-xs font-medium"
                  style={{ color: "var(--accent)" }}
                >
                  View →
                </Link>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard label="Products" value={summary.portfolio.length} />
        <StatCard label="Open tasks" value={summary.operations.open_tasks} />
        <StatCard label="Active workflow runs" value={summary.operations.active_workflow_runs} />
        <StatCard label="Pending approvals" value={summary.operations.pending_approvals} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Finance snapshot" />
          <div className="grid grid-cols-3 gap-3">
            <MiniStat
              label="Revenue"
              value={formatMoney(summary.finance.revenue_cents, summary.finance.currency)}
            />
            <MiniStat
              label="Expenses"
              value={formatMoney(summary.finance.expense_cents, summary.finance.currency)}
            />
            <MiniStat
              label="Margin"
              value={formatMoney(summary.finance.margin_cents, summary.finance.currency)}
              tone={summary.finance.margin_cents < 0 ? "danger" : "success"}
            />
          </div>
          <Link
            href="/finance"
            className="mt-3 inline-block text-xs font-medium"
            style={{ color: "var(--accent)" }}
          >
            Open finance ledger →
          </Link>
        </Card>

        <Card>
          <CardHeader title="AI activity" description="This workspace, all time" />
          {!usage || usage.total_calls === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              No AI usage recorded yet.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              <MiniStat label="Calls" value={String(usage.total_calls)} />
              <MiniStat label="Tokens in" value={usage.total_tokens_in.toLocaleString()} />
              <MiniStat label="Tokens out" value={usage.total_tokens_out.toLocaleString()} />
            </div>
          )}
          <Link
            href="/ai"
            className="mt-3 inline-block text-xs font-medium"
            style={{ color: "var(--accent)" }}
          >
            Open AI Settings →
          </Link>
        </Card>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Product portfolio" />
          {summary.portfolio.length === 0 ? (
            <EmptyState message="No products yet." />
          ) : (
            <div className="space-y-2">
              {summary.portfolio.map((p) => {
                const openWork = p.task_counts.todo + p.task_counts.in_progress + p.task_counts.blocked;
                return (
                  <Link
                    key={p.product_id}
                    href={`/products/${p.product_id}`}
                    className="flex items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
                  >
                    <div>
                      <div className="font-medium">{p.name}</div>
                      <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                        {p.stage} · {p.active_project_count} active project
                        {p.active_project_count === 1 ? "" : "s"}
                      </div>
                    </div>
                    <Badge tone={p.task_counts.blocked > 0 ? "warning" : "neutral"}>
                      {openWork} open
                    </Badge>
                  </Link>
                );
              })}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader title="Recent workflow runs" />
          {summary.recent_workflow_runs.length === 0 ? (
            <EmptyState message="No workflow runs yet." />
          ) : (
            <div className="space-y-2">
              {summary.recent_workflow_runs.map((run) => (
                <Link
                  key={run.id}
                  href={`/workflows/${run.id}`}
                  className="flex items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
                >
                  <span className="font-medium">{run.graph_name}</span>
                  <Badge tone={run.status === "failed" ? "danger" : run.status === "completed" ? "success" : "neutral"}>
                    {run.status}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function QuickActions() {
  const actions = [
    { href: "/workflows", label: "Start a workflow" },
    { href: "/finance", label: "Add an expense" },
    { href: "/compliance", label: "Add compliance item" },
    { href: "/tasks", label: "Add a task" },
  ];
  return (
    <div className="mb-6 flex flex-wrap gap-2">
      {actions.map((a) => (
        <Link
          key={a.href}
          href={a.href}
          className="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
          style={{
            backgroundColor: "var(--accent-soft)",
            color: "var(--accent)",
          }}
        >
          {a.label}
        </Link>
      ))}
    </div>
  );
}

type AttentionItem = {
  key: string;
  title: string;
  detail?: string;
  href: string;
  badge: string;
  tone: "danger" | "warning" | "accent";
};

function buildAttentionItems(summary: CeoSummary): AttentionItem[] {
  const items: AttentionItem[] = [];

  if (summary.operations.pending_approvals > 0) {
    items.push({
      key: "approvals",
      title: `${summary.operations.pending_approvals} workflow approval${summary.operations.pending_approvals === 1 ? "" : "s"} waiting on you`,
      href: "/workflows",
      badge: "approval",
      tone: "accent",
    });
  }

  if (summary.operations.overdue_tasks > 0) {
    items.push({
      key: "overdue-tasks",
      title: `${summary.operations.overdue_tasks} task${summary.operations.overdue_tasks === 1 ? "" : "s"} overdue`,
      href: "/tasks",
      badge: "overdue",
      tone: "danger",
    });
  }

  if (summary.operations.blocked_tasks > 0) {
    items.push({
      key: "blocked-tasks",
      title: `${summary.operations.blocked_tasks} task${summary.operations.blocked_tasks === 1 ? "" : "s"} blocked`,
      href: "/tasks",
      badge: "blocked",
      tone: "warning",
    });
  }

  for (const o of summary.compliance_overdue) {
    items.push({
      key: `compliance-${o.id}`,
      title: o.title,
      detail: `Compliance · due ${o.due_date ?? "unknown"}`,
      href: "/compliance",
      badge: "overdue",
      tone: "danger",
    });
  }

  return items;
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <div className="text-sm" style={{ color: "var(--text-tertiary)" }}>
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </Card>
  );
}

function MiniStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "success" | "danger";
}) {
  return (
    <div>
      <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>
        {label}
      </div>
      <div
        className="mt-0.5 text-lg font-semibold"
        style={tone ? { color: `var(--${tone})` } : undefined}
      >
        {value}
      </div>
    </div>
  );
}
