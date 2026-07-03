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
      try {
        const list = await refreshCompanies();
        const stored = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
        const stillExists = stored && list.some((c) => c.id === stored);
        setActiveCompanyIdState(stillExists ? stored : (list[0]?.id ?? null));
      } catch {
        // Backend not reachable yet — pages render their own empty states.
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
