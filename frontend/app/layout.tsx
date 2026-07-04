import type { Metadata } from "next";
import "./globals.css";
import { CompanyProvider } from "@/lib/company-context";
import { AuthProvider } from "@/lib/auth-context";
import { Sidebar } from "@/components/Sidebar";
import { CompanySwitcher } from "@/components/CompanySwitcher";
import { AuthStatus } from "@/components/AuthStatus";
import { AuthGate } from "@/components/AuthGate";

export const metadata: Metadata = {
  title: "JAIOS — Jyka AI Operating System",
  description: "Company-wide agentic operating system for Jyka Labs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <CompanyProvider>
          <AuthProvider>
            <div className="flex h-screen">
              <Sidebar />
              <div className="flex flex-1 flex-col overflow-hidden">
                <header className="flex items-center justify-end gap-4 border-b border-neutral-200 px-6 py-3 dark:border-neutral-800">
                  <CompanySwitcher />
                  <AuthStatus />
                </header>
                <main className="flex-1 overflow-y-auto p-6">
                  <AuthGate>{children}</AuthGate>
                </main>
              </div>
            </div>
          </AuthProvider>
        </CompanyProvider>
      </body>
    </html>
  );
}
