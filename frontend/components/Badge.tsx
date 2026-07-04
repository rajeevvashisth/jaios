type BadgeTone = "neutral" | "accent" | "success" | "warning" | "danger";

const TONE_STYLES: Record<BadgeTone, { bg: string; fg: string }> = {
  neutral: { bg: "var(--border-subtle)", fg: "var(--text-secondary)" },
  accent: { bg: "var(--accent-soft)", fg: "var(--accent)" },
  success: { bg: "var(--success-soft)", fg: "var(--success)" },
  warning: { bg: "var(--warning-soft)", fg: "var(--warning)" },
  danger: { bg: "var(--danger-soft)", fg: "var(--danger)" },
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  const style = TONE_STYLES[tone];
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: style.bg, color: style.fg }}
    >
      {children}
    </span>
  );
}

/** Maps a compliance/task "urgency"-shaped string to a sensible tone
 * without every page needing its own switch statement. */
export function toneForUrgency(urgency: string): BadgeTone {
  switch (urgency) {
    case "overdue":
      return "danger";
    case "due_soon":
      return "warning";
    case "completed":
      return "success";
    case "review_pending":
      return "accent";
    default:
      return "neutral";
  }
}
