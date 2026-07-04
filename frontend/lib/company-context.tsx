"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Company } from "@/lib/api";

const STORAGE_KEY = "jaios_company_id";

type CompanyContextValue = {
  companies: Company[];
  activeCompanyId: string | null;
  setActiveCompanyId: (id: string) => void;
  refreshCompanies: () => Promise<Company[]>;
  loading: boolean;
};

const CompanyContext = createContext<CompanyContextValue | null>(null);

export function CompanyProvider({ children }: { children: ReactNode }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompanyId, setActiveCompanyIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshCompanies = async () => {
    const list = await api.companies.list();
    setCompanies(list);
    return list;
  };

  useEffect(() => {
    (async () => {
      const stored = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
      try {
        const list = await refreshCompanies();
        const stillExists = stored && list.some((c) => c.id === stored);
        setActiveCompanyIdState(stillExists ? stored : (list[0]?.id ?? stored ?? null));
      } catch {
        // GET /companies requires auth (it only ever returns the caller's
        // own company) — before sign-in, or if the backend isn't reachable
        // yet, fall back to whatever was last remembered locally so the
        // login/register flow (which needs a company_id to register
        // against) still works without a fetched company list.
        setActiveCompanyIdState(stored);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const setActiveCompanyId = (id: string) => {
    setActiveCompanyIdState(id);
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, id);
  };

  return (
    <CompanyContext.Provider
      value={{ companies, activeCompanyId, setActiveCompanyId, refreshCompanies, loading }}
    >
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) throw new Error("useCompany must be used within a CompanyProvider");
  return ctx;
}
