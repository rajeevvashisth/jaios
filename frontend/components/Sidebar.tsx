"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Boxes,
  Brain,
  Calculator,
  Cog,
  Cpu,
  FolderKanban,
  Gauge,
  ListTodo,
  ScrollText,
  ShieldCheck,
  Sparkles,
  Workflow,
  type LucideIcon,
} from "lucide-react";

const NAV_SECTIONS: { label: string; items: { href: string; label: string; icon: LucideIcon }[] }[] = [
  {
    label: "",
    items: [{ href: "/", label: "Command Center", icon: Gauge }],
  },
  {
    label: "Business",
    items: [
      { href: "/products", label: "Products", icon: Boxes },
      { href: "/projects", label: "Projects", icon: FolderKanban },
      { href: "/tasks", label: "Tasks", icon: ListTodo },
      { href: "/workflows", label: "Workflows", icon: Workflow },
    ],
  },
  {
    label: "Finance & Compliance",
    items: [
      { href: "/finance", label: "Finance", icon: Calculator },
      { href: "/compliance", label: "Compliance", icon: ShieldCheck },
    ],
  },
  {
    label: "Knowledge & AI",
    items: [
      { href: "/knowledge", label: "Knowledge", icon: Brain },
      { href: "/memory", label: "Memory / Activity", icon: ScrollText },
      { href: "/agents", label: "Agents", icon: Cpu },
      { href: "/ai", label: "AI Settings", icon: Sparkles },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/logs", label: "Logs / Traces", icon: ScrollText },
      { href: "/settings", label: "Settings", icon: Cog },
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
          className="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold"
          style={{
            background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
            color: "var(--accent-contrast)",
          }}
        >
          J
        </span>
        <span className="font-heading text-base font-semibold tracking-tight">JAIOS</span>
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
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="relative flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors"
                  style={
                    active
                      ? { backgroundColor: "var(--accent-soft)", color: "var(--accent)" }
                      : { color: "var(--text-secondary)" }
                  }
                >
                  <Icon size={16} strokeWidth={2} className="shrink-0" />
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
