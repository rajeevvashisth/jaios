"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

/** Small orientation cue in the header — which workspace am I in? Silently
 * renders nothing if not signed in or the fetch fails, since this is a
 * nice-to-have, not load-bearing for any page. */
export function WorkspaceLabel() {
  const { user } = useAuth();
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setName(null);
      return;
    }
    api.workspaces
      .getMine()
      .then((ws) => setName(ws.name))
      .catch(() => setName(null));
  }, [user]);

  if (!name) return null;

  return (
    <div
      className="mr-auto flex items-center gap-1.5 text-sm font-medium"
      style={{ color: "var(--text-secondary)" }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: "var(--accent)" }}
        aria-hidden
      />
      {name}
    </div>
  );
}
