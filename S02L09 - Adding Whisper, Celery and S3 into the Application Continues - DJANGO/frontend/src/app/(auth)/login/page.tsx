"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AuthArtwork } from "@/components/AuthArtwork";
import { useAuth } from "@/components/AuthProvider";
import { ApiError } from "@/lib/api";

function LoginForm() {
  const { ready, authenticated, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (ready && authenticated) router.replace("/dashboard");
  }, [ready, authenticated, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 403 && /confirm/i.test(err.message)) {
        const params = new URLSearchParams({ email });
        router.replace(`/confirm?${params.toString()}`);
        return;
      }
      setFormError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
        Welcome back
      </h1>
      <p className="mt-1.5 text-sm text-ink-500">
        Sign in to your Subly account.
      </p>

      <form onSubmit={onSubmit} className="mt-7 space-y-4">
        <div>
          <label className="block text-sm font-medium text-ink-700" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input mt-1.5 w-full"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-ink-700" htmlFor="password">
              Password
            </label>
            <Link
              href={`/forgot-password${
                email ? `?email=${encodeURIComponent(email)}` : ""
              }`}
              className="text-sm font-semibold text-brand-600 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input mt-1.5 w-full"
            placeholder="••••••••"
          />
        </div>

        {formError && (
          <p className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-600">
            {formError}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || !ready}
          className="btn-primary w-full !rounded-lg justify-center disabled:opacity-60"
        >
          {submitting ? "Signing in…" : "Log in"}
        </button>

        <p className="text-center text-sm text-ink-500">
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="font-semibold text-brand-600 hover:underline"
          >
            Sign up
          </Link>
        </p>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <>
      <section className="flex flex-1 items-center justify-center">
        <Suspense fallback={<div className="w-full max-w-sm" />}>
          <LoginForm />
        </Suspense>
      </section>

      <AuthArtwork variant="login" />
    </>
  );
}
