"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useCompany } from "@/lib/company-context";
import { PageHeader } from "@/components/PageHeader";

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuth();
  const { activeCompanyId } = useCompany();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        if (!activeCompanyId) {
          setError("Create or select a company in Settings first.");
          return;
        }
        await register(activeCompanyId, email, password);
      }
      router.push("/");
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-sm">
      <PageHeader
        title={mode === "login" ? "Sign in" : "Create account"}
        description="Human sign-off on workflow approvals requires an identified account."
      />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-neutral-500">Email</label>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
          />
        </div>
        <div>
          <label className="block text-sm text-neutral-500">Password</label>
          <input
            required
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm dark:border-neutral-700"
          />
        </div>
        {error && <p className="text-sm text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
        >
          {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>

      <button
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        className="mt-4 text-sm text-neutral-500 underline"
      >
        {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
      </button>
    </div>
  );
}
