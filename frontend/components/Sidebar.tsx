"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/agents", label: "Agents" },
  { href: "/tasks", label: "Tasks" },
  { href: "/projects", label: "Projects" },
  { href: "/products", label: "Products" },
  { href: "/finance", label: "Finance" },
  { href: "/compliance", label: "Compliance" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/memory", label: "Memory / Activity" },
  { href: "/workflows", label: "Workflows" },
  { href: "/logs", label: "Logs / Traces" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex h-full w-56 shrink-0 flex-col gap-1 border-r border-neutral-200 p-4 dark:border-neutral-800">
      <div className="mb-4 px-2 text-lg font-semibold">JAIOS</div>
      {NAV_ITEMS.map((item) => {
        const active =
          pathname === item.href || (item.href !== "/" && pathname?.startsWith(`${item.href}/`));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-md px-2 py-1.5 text-sm ${
              active
                ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900"
                : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-900"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
