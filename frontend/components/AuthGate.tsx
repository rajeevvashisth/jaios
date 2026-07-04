"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

// /login obviously has to render while signed out. /settings also has to:
// it's the only place to create the very first company (POST /companies
// is intentionally unauthenticated, since there's no user to authenticate
// as until one is registered against a company_id — see backend
// companies.py). Every other page reads data that now requires auth.
const PUBLIC_PATHS = ["/login", "/settings"];

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();

  if (loading || PUBLIC_PATHS.includes(pathname)) {
    return <>{children}</>;
  }

  if (!user) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
        <p className="text-sm text-neutral-500">
          Sign in to use JAIOS — almost everything here is scoped to your company account.
        </p>
        <Link
          href="/login"
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white dark:bg-neutral-100 dark:text-neutral-900"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
