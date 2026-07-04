"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_SECTIONS: { label: string; items: { href: string; label: string }[] }[] = [
  {
    label: "",
    items: [{ href: "/", label: "Command Center" }],
  },
  {
    label: "Business",
    items: [
      { href: "/products", label: "Products" },
      { href: "/projects", label: "Projects" },
      { href: "/tasks", label: "Tasks" },
      { href: "/workflows", label: "Workflows" },
    ],
  },
  {
    label: "Finance & Compliance",
    items: [
      { href: "/finance", label: "Finance" },
      { href: "/compliance", label: "Compliance" },
    ],
  },
  {
    label: "Knowledge & AI",
    items: [
      { href: "/knowledge", label: "Knowledge" },
      { href: "/memory", label: "Memory / Activity" },
      { href: "/agents", label: "Agents" },
      { href: "/ai", label: "AI Settings" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/logs", label: "Logs / Traces" },
      { href: "/settings", label: "Settings" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav
      className="flex h-full w-60 shrink-0 flex-col gap-5 overflow-y-auto p-4"
      style={{ borderRight: "1px solid var(--border-subtle)", backgroundColor: "var(--surface)" }}
    >
      <Link href="/" className="mb-1 flex items-center gap-2 px-2">
        <span
          className="flex h-6 w-6 items-center justify-center rounded-md text-xs font-bold"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-contrast)" }}
        >
          J
        </span>
        <span className="text-base font-semibold tracking-tight">JAIOS</span>
      </Link>

      {NAV_SECTIONS.map((section) => (
        <div key={section.label || "root"}>
          {section.label && (
            <div
              className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: "var(--text-tertiary)" }}
            >
              {section.label}
            </div>
          )}
          <div className="flex flex-col gap-0.5">
            {section.items.map((item) => {
              const active =
                pathname === item.href ||
                (item.href !== "/" && pathname?.startsWith(`${item.href}/`));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="relative rounded-md px-2 py-1.5 text-sm transition-colors"
                  style={
                    active
                      ? { backgroundColor: "var(--accent-soft)", color: "var(--accent)" }
                      : { color: "var(--text-secondary)" }
                  }
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}
