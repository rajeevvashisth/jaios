const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_STORAGE_KEY = "jaios_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const res = await fetch(`${API_BASE_URL}/api${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type Company = {
  id: string;
  name: string;
  mission: string | null;
  strategic_goals: string[];
};

export type Product = {
  id: string;
  company_id: string;
  name: string;
  type: string;
  stage: string;
  owner: string | null;
  status: string;
  description: string | null;
  roadmap: string[];
};

export type Project = {
  id: string;
  company_id: string;
  product_id: string | null;
  name: string;
  goal: string | null;
  status: string;
  start_date: string | null;
  target_date: string | null;
};

export type Task = {
  id: string;
  company_id: string;
  project_id: string | null;
  product_id: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assignee_agent_key: string | null;
  assignee_human: string | null;
  due_date: string | null;
};

export type AgentSpec = {
  key: string;
  name: string;
  layer: string;
  responsibility: string;
  allowed_tools: string[];
  memory_scope: string;
  can_delegate_to: string[];
  requires_approval_for: string[];
  escalates_to: string | null;
  enabled: boolean;
  last_active_at: string | null;
};

export type WorkflowRun = {
  id: string;
  graph_name: string;
  thread_id: string;
  status: string;
  initiating_actor: string;
  company_id: string;
  task_id: string | null;
  project_id: string | null;
  started_at: string;
  completed_at: string | null;
};

export type WorkflowStep = {
  id: string;
  workflow_run_id: string;
  agent_key: string;
  step_index: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  status: string;
  started_at: string;
  completed_at: string | null;
};

export type ApprovalRequest = {
  id: string;
  workflow_run_id: string;
  workflow_step_id: string | null;
  action_type: string;
  requested_by_agent_key: string;
  summary: string;
  status: string;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
};

export type MemoryRecord = {
  id: string;
  scope_type: string;
  scope_id: string;
  agent_key: string | null;
  kind: string;
  content: Record<string, unknown>;
  created_at: string;
  expires_at: string | null;
};

export type AuditLogEntry = {
  id: string;
  occurred_at: string;
  actor_type: string;
  actor_key: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  tool_used: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  workflow_run_id: string | null;
};

export type KnowledgeSearchResult = {
  document_id: string;
  document_title: string;
  chunk_index: number;
  content: string;
  score: number;
};

export type FinanceEntry = {
  id: string;
  company_id: string;
  product_id: string | null;
  entry_type: "revenue" | "expense" | "capital";
  category: string;
  amount_cents: number;
  currency: string;
  description: string | null;
  occurred_on: string;
  is_recurring: boolean;
  recurrence_interval: string | null;
};

export type CategoryBreakdown = { category: string; amount_cents: number };

export type FinanceSummary = {
  company_id: string;
  product_id: string | null;
  currency: string;
  revenue_cents: number;
  expense_cents: number;
  margin_cents: number;
  capital_cents: number;
  revenue_by_category: CategoryBreakdown[];
  expense_by_category: CategoryBreakdown[];
  capital_by_category: CategoryBreakdown[];
};

export type ComplianceUrgency = "completed" | "overdue" | "due_soon" | "upcoming";

export type ComplianceObligation = {
  id: string;
  company_id: string;
  product_id: string | null;
  title: string;
  category: string;
  owner_agent_key: string | null;
  due_date: string;
  completed: boolean;
  completed_at: string | null;
  recurrence: string;
  notes: string | null;
  urgency: ComplianceUrgency;
};

export type TaskStatusCounts = {
  todo: number;
  in_progress: number;
  blocked: number;
  done: number;
};

export type ProductPortfolioEntry = {
  product_id: string;
  name: string;
  type: string;
  stage: string;
  status: string;
  task_counts: TaskStatusCounts;
  active_project_count: number;
};

export type OperationsHealth = {
  open_tasks: number;
  overdue_tasks: number;
  blocked_tasks: number;
  active_workflow_runs: number;
  pending_approvals: number;
};

export type CeoSummary = {
  company_id: string;
  portfolio: ProductPortfolioEntry[];
  finance: FinanceSummary;
  operations: OperationsHealth;
  compliance_overdue: ComplianceObligation[];
  compliance_due_soon: ComplianceObligation[];
  recent_workflow_runs: WorkflowRun[];
};

export type ProductStatusReport = {
  product_id: string;
  name: string;
  stage: string;
  status: string;
  task_counts: TaskStatusCounts;
  project_count: number;
  finance: FinanceSummary;
  compliance_obligations: ComplianceObligation[];
};

export type UserRole = "admin" | "member" | "viewer";

export type User = {
  id: string;
  company_id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
};

export const api = {
  companies: {
    list: () => request<Company[]>("/companies"),
    create: (payload: { name: string; mission?: string }) =>
      request<Company>("/companies", { method: "POST", body: JSON.stringify(payload) }),
  },
  products: {
    list: (companyId?: string) =>
      request<Product[]>(`/products${companyId ? `?company_id=${companyId}` : ""}`),
    get: (productId: string) => request<Product>(`/products/${productId}`),
    create: (payload: Partial<Product> & { name: string; company_id: string }) =>
      request<Product>("/products", { method: "POST", body: JSON.stringify(payload) }),
  },
  projects: {
    list: (companyId?: string) =>
      request<Project[]>(`/projects${companyId ? `?company_id=${companyId}` : ""}`),
    create: (payload: Partial<Project> & { name: string; company_id: string }) =>
      request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  },
  tasks: {
    list: (companyId?: string) =>
      request<Task[]>(`/tasks${companyId ? `?company_id=${companyId}` : ""}`),
    create: (payload: Partial<Task> & { title: string; company_id: string }) =>
      request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
    route: (taskId: string) =>
      request<Task>(`/tasks/${taskId}/route`, { method: "POST" }),
  },
  agents: {
    list: () => request<AgentSpec[]>("/agents"),
  },
  workflows: {
    graphs: () => request<string[]>("/workflows/graphs"),
    list: (companyId?: string) =>
      request<WorkflowRun[]>(`/workflows${companyId ? `?company_id=${companyId}` : ""}`),
    get: (runId: string) => request<WorkflowRun>(`/workflows/${runId}`),
    steps: (runId: string) => request<WorkflowStep[]>(`/workflows/${runId}/steps`),
    pendingApprovals: () => request<ApprovalRequest[]>("/workflows/approvals/pending"),
    start: (payload: {
      graph_name: string;
      company_id: string;
      goal: string;
      task_id?: string;
      project_id?: string;
      workspace_path?: string;
      initiating_actor?: string;
    }) =>
      request<WorkflowRun>("/workflows/start", {
        method: "POST",
        body: JSON.stringify({
          graph_name: payload.graph_name,
          company_id: payload.company_id,
          task_id: payload.task_id,
          project_id: payload.project_id,
          workspace_path: payload.workspace_path,
          initiating_actor: payload.initiating_actor ?? "human",
          input: { goal: payload.goal },
        }),
      }),
    // `decided_by` is derived server-side from the authenticated user — the
    // caller must be signed in (see lib/auth-context.tsx); there is no
    // client-supplied identity field to spoof.
    decide: (runId: string, payload: { approve: boolean; note?: string }) =>
      request<WorkflowRun>(`/workflows/${runId}/approve`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  memory: {
    list: (scopeType: string, scopeId: string) =>
      request<MemoryRecord[]>(`/memory?scope_type=${scopeType}&scope_id=${scopeId}`),
  },
  knowledge: {
    ingest: (payload: {
      company_id: string;
      title: string;
      source_type: string;
      content: string;
    }) =>
      request<{ id: string }>("/knowledge/documents", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    search: (payload: { company_id: string; query: string; top_k?: number }) =>
      request<KnowledgeSearchResult[]>("/knowledge/search", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
  audit: {
    list: (limit = 100) => request<AuditLogEntry[]>(`/audit?limit=${limit}`),
  },
  finance: {
    listEntries: (companyId: string, productId?: string) =>
      request<FinanceEntry[]>(
        `/finance/entries?company_id=${companyId}${productId ? `&product_id=${productId}` : ""}`
      ),
    createEntry: (payload: {
      company_id: string;
      product_id?: string;
      entry_type: "revenue" | "expense" | "capital";
      category: string;
      amount_cents: number;
      currency?: string;
      description?: string;
      occurred_on: string;
      is_recurring?: boolean;
    }) =>
      request<FinanceEntry>("/finance/entries", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    summary: (companyId: string, productId?: string) =>
      request<FinanceSummary>(
        `/finance/summary?company_id=${companyId}${productId ? `&product_id=${productId}` : ""}`
      ),
  },
  compliance: {
    listObligations: (companyId: string, opts?: { productId?: string; includeCompleted?: boolean }) =>
      request<ComplianceObligation[]>(
        `/compliance/obligations?company_id=${companyId}` +
          (opts?.productId ? `&product_id=${opts.productId}` : "") +
          (opts?.includeCompleted ? "&include_completed=true" : "")
      ),
    create: (payload: {
      company_id: string;
      product_id?: string;
      title: string;
      category: string;
      owner_agent_key?: string;
      due_date: string;
      recurrence?: string;
      notes?: string;
    }) =>
      request<ComplianceObligation>("/compliance/obligations", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    complete: (obligationId: string) =>
      request<ComplianceObligation>(`/compliance/obligations/${obligationId}/complete`, {
        method: "POST",
      }),
  },
  reports: {
    ceoSummary: (companyId: string) =>
      request<CeoSummary>(`/reports/ceo-summary?company_id=${companyId}`),
    productStatus: (productId: string) =>
      request<ProductStatusReport>(`/reports/product-status/${productId}`),
  },
  auth: {
    register: (payload: { company_id: string; email: string; password: string }) =>
      request<User>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
    login: (payload: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    me: () => request<User>("/auth/me"),
  },
};
