"""Process-wide Prometheus metrics.

A small, fixed set of counters/histograms covering the things an operator
actually wants to alert on: request volume/latency, agent turns, tool
calls, and workflow run/approval outcomes. Exposed at ``GET /metrics`` in
the standard Prometheus text format — point a Prometheus server (or a
Grafana Agent) at it, no push gateway needed. See docs/architecture.md for
how this composes with the audit log (per-action detail) vs. metrics
(aggregate rates).
"""

from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "jaios_http_requests_total",
    "HTTP requests handled, by method/path template/status.",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "jaios_http_request_duration_seconds",
    "HTTP request latency in seconds, by method/path template.",
    ["method", "path"],
)

agent_turns_total = Counter(
    "jaios_agent_turns_total",
    "Agent node executions, by agent key.",
    ["agent_key"],
)

tool_calls_total = Counter(
    "jaios_tool_calls_total",
    "Tool invocations, by tool key and outcome (success/failure/denied).",
    ["tool_key", "outcome"],
)

workflow_runs_total = Counter(
    "jaios_workflow_runs_total",
    "Completed workflow runs, by graph name and final status.",
    ["graph_name", "status"],
)

approval_decisions_total = Counter(
    "jaios_approval_decisions_total",
    "Approval requests decided, by action type and decision.",
    ["action_type", "decision"],
)
