"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type Project, type Task } from "@/lib/api";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";

const PRIORITIES = ["low", "medium", "high", "urgent"];

export default function TasksPage() {
  const { activeCompanyId } = useCompany();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(PRIORITIES[1]);
  const [projectId, setProjectId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startedRunId, setStartedRunId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!activeCompanyId) return;
    api.tasks.list(activeCompanyId).then(setTasks);
    api.projects.list(activeCompanyId).then(setProjects);
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
      await api.tasks.create({
        company_id: activeCompanyId,
        project_id: projectId || undefined,
        title,
        description: description || undefined,
        priority: priority as Task["priority"],
      });
      setTitle("");
      setDescription("");
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRoute(taskId: string) {
    setBusyTaskId(taskId);
    try {
      await api.tasks.route(taskId);
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyTaskId(null);
    }
  }

  async function handleStartWorkflow(task: Task) {
    if (!activeCompanyId) return;
    setBusyTaskId(task.id);
    setError(null);
    try {
      const run = await api.workflows.start({
        graph_name: "task_delegation",
        company_id: activeCompanyId,
        goal: task.title,
        task_id: task.id,
      });
      setStartedRunId(run.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusyTaskId(null);
    }
  }

  if (!activeCompanyId) {
    return (
      <div>
        <PageHeader title="Tasks" description="Company-wide task list across products and projects." />
        <EmptyState message="Create a company in Settings to get started." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Tasks" description="Company-wide task list across products and projects." />

      <form onSubmit={handleCreate} className="mb-8 flex flex-wrap items-end gap-3">
        <div className="min-w-[220px] flex-1">
          <label className="block text-xs text-neutral-500">Title</label>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ship pricing page"
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div className="min-w-[220px] flex-1">
          <label className="block text-xs text-neutral-500">Description</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-neutral-500">Project</label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="mt-1 rounded-md border border-neutral-300 bg-transparent px-2 py-1.5 text-sm dark:border-neutral-700"
          >
            <option value="">Unassigned</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Adding…" : "Add task"}
        </button>
      </form>
      {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
      {startedRunId && (
        <p className="mb-4 text-sm text-green-600">
          Workflow started —{" "}
          <Link href={`/workflows/${startedRunId}`} className="underline">
            view trace
          </Link>
          .
        </p>
      )}

      {tasks.length === 0 ? (
        <EmptyState message="No tasks yet." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-neutral-500">
            <tr>
              <th className="pb-2">Title</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Priority</th>
              <th className="pb-2">Assignee</th>
              <th className="pb-2">Due</th>
              <th className="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id} className="border-t border-neutral-200 dark:border-neutral-800">
                <td className="py-2">{task.title}</td>
                <td className="py-2">{task.status}</td>
                <td className="py-2">{task.priority}</td>
                <td className="py-2">{task.assignee_agent_key ?? task.assignee_human ?? "—"}</td>
                <td className="py-2">{task.due_date ?? "—"}</td>
                <td className="flex gap-2 py-2">
                  <button
                    onClick={() => handleRoute(task.id)}
                    disabled={busyTaskId === task.id}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-neutral-700"
                  >
                    Route
                  </button>
                  <button
                    onClick={() => handleStartWorkflow(task)}
                    disabled={busyTaskId === task.id}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-xs disabled:opacity-50 dark:border-neutral-700"
                  >
                    Start workflow
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
