import type { Metadata } from "next";
import { JetBrains_Mono, Sora } from "next/font/google";
import "./globals.css";
import { CompanyProvider } from "@/lib/company-context";
import { AuthProvider } from "@/lib/auth-context";
import { Sidebar } from "@/components/Sidebar";
import { CompanySwitcher } from "@/components/CompanySwitcher";
import { AuthStatus } from "@/components/AuthStatus";
import { AuthGate } from "@/components/AuthGate";
import { WorkspaceLabel } from "@/components/WorkspaceLabel";

// A geometric sans for headings/nav/brand (distinct from the body's system
// font stack — this is what breaks the "every AI-generated dashboard looks
// identical" sameness) and a monospace for numbers/ids/data, which reads
// as "engineered" rather than templated. Both self-hosted by Next at
// build time — no runtime calls to Google's CDN.
const sora = Sora({ subsets: ["latin"], variable: "--font-heading", weight: ["500", "600", "700"] });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["400", "500", "600"] });

export const metadata: Metadata = {
  title: "JAIOS — AI Operating System",
  description: "An AI operating system for running a company — Jyka Labs LLP's first workspace",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${jetbrainsMono.variable}`}>
      <body>
        <CompanyProvider>
          <AuthProvider>
            <div className="flex h-screen" style={{ backgroundColor: "var(--surface-sunken)" }}>
              <Sidebar />
              <div className="flex flex-1 flex-col overflow-hidden">
                <header
                  className="flex items-center gap-4 px-6 py-3"
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    backgroundColor: "var(--surface)",
                  }}
                >
                  <WorkspaceLabel />
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
