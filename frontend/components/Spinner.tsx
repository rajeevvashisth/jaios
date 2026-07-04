export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-sm" style={{ color: "var(--text-tertiary)" }}>
      <span
        className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
        style={{ borderTopColor: "transparent" }}
        aria-hidden
      />
      {label}
    </div>
  );
}
