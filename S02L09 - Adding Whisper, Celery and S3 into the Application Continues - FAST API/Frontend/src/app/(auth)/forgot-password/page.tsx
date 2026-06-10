"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthArtwork } from "@/components/AuthArtwork";
import { useAuth } from "@/components/AuthProvider";

export default function ForgotPasswordPage() {
  const { forgotPassword } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await forgotPassword(email);
      const params = new URLSearchParams({ email });
      router.replace(`/reset-password?${params.toString()}`);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not send code");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <section className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-sm">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
            Forgot your password?
          </h1>
          <p className="mt-1.5 text-sm text-ink-500">
            Enter your email and we&apos;ll send you a code to reset it.
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

            {formError && (
              <p className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-600">
                {formError}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full !rounded-lg justify-center disabled:opacity-60"
            >
              {submitting ? "Sending…" : "Send reset code"}
            </button>

            <p className="text-center text-sm text-ink-500">
              Remembered it?{" "}
              <Link
                href="/login"
                className="font-semibold text-brand-600 hover:underline"
              >
                Log in
              </Link>
            </p>
          </form>
        </div>
      </section>

      <AuthArtwork variant="login" />
    </>
  );
}
