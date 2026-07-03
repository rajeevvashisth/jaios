"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, getStoredToken, setStoredToken, type User } from "@/lib/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (companyId: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      if (!getStoredToken()) {
        setLoading(false);
        return;
      }
      try {
        setUser(await api.auth.me());
      } catch {
        setStoredToken(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.auth.login({ email, password });
    setStoredToken(access_token);
    setUser(await api.auth.me());
  }

  async function register(companyId: string, email: string, password: string) {
    await api.auth.register({ company_id: companyId, email, password });
    await login(email, password);
  }

  function logout() {
    setStoredToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
