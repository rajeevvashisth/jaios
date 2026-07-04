export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-7">
      <h1 className="font-heading text-2xl font-semibold tracking-tight">{title}</h1>
      {description && (
        <p className="mt-1.5 text-sm" style={{ color: "var(--text-secondary)" }}>
          {description}
        </p>
      )}
    </div>
  );
}
