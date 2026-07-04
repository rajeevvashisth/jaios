import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANT_STYLE: Record<Variant, { bg: string; fg: string; border?: string }> = {
  primary: { bg: "var(--accent)", fg: "var(--accent-contrast)" },
  secondary: { bg: "transparent", fg: "var(--text-primary)", border: "var(--border-default)" },
  danger: { bg: "transparent", fg: "var(--danger)", border: "var(--danger)" },
  ghost: { bg: "transparent", fg: "var(--text-secondary)" },
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm" | "md";
};

export function Button({ variant = "secondary", size = "md", className = "", style, ...rest }: Props) {
  const v = VARIANT_STYLE[variant];
  const sizeClass = size === "sm" ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm";
  return (
    <button
      className={`rounded-md font-medium transition-opacity disabled:cursor-not-allowed disabled:opacity-50 ${sizeClass} ${className}`}
      style={{
        backgroundColor: v.bg,
        color: v.fg,
        border: v.border ? `1px solid ${v.border}` : "1px solid transparent",
        ...style,
      }}
      {...rest}
    />
  );
}
