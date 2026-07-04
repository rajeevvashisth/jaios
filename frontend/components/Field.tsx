import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

const fieldStyle = {
  backgroundColor: "transparent",
  border: "1px solid var(--border-default)",
  color: "var(--text-primary)",
};

export function Label({ children }: { children: ReactNode }) {
  return (
    <label className="mb-1 block text-xs" style={{ color: "var(--text-tertiary)" }}>
      {children}
    </label>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className = "", ...rest } = props;
  return (
    <input
      className={`rounded-md px-3 py-1.5 text-sm outline-none focus:ring-2 ${className}`}
      style={{ ...fieldStyle, ["--tw-ring-color" as string]: "var(--accent)" }}
      {...rest}
    />
  );
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  const { className = "", ...rest } = props;
  return (
    <select
      className={`rounded-md px-2 py-1.5 text-sm outline-none focus:ring-2 ${className}`}
      style={{ ...fieldStyle, ["--tw-ring-color" as string]: "var(--accent)" }}
      {...rest}
    />
  );
}
