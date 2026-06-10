"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { ready, authenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !authenticated) {
      router.replace("/login");
    }
  }, [ready, authenticated, router]);

  if (!ready) {
    return (
      <div className="grid min-h-[40vh] place-items-center text-sm text-ink-500">
        Loading…
      </div>
    );
  }
  if (!authenticated) {
    return null;
  }
  return <>{children}</>;
}
