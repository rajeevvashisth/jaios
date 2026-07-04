import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return <div className={`jaios-card ${padded ? "p-4" : ""} ${className}`}>{children}</div>;
}

export function CardHeader({
  title,
  action,
  description,
}: {
  title: string;
  action?: ReactNode;
  description?: string;
}) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
          {title}
        </h2>
        {description && (
          <p className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}
