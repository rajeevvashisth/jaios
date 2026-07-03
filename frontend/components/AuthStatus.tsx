"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export function AuthStatus() {
  const { user, loading, logout } = useAuth();

  if (loading) return null;

  if (!user) {
    return (
      <Link href="/login" className="text-sm text-neutral-500 underline">
        Sign in
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-neutral-500">
        {user.email} <span className="text-xs">({user.role})</span>
      </span>
      <button onClick={logout} className="text-neutral-500 underline">
        Sign out
      </button>
    </div>
  );
}
