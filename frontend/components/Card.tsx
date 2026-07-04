import type { CSSProperties, ReactNode } from "react";

export function Card({
  children,
  className = "",
  padded = true,
  style,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
  style?: CSSProperties;
}) {
  return (
    <div className={`jaios-card ${padded ? "p-4" : ""} ${className}`} style={style}>
      {children}
    </div>
  );
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
        <h2 className="font-heading text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
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
