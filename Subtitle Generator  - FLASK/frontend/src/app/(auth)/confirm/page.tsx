"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AuthArtwork } from "@/components/AuthArtwork";
import { useAuth } from "@/components/AuthProvider";

function ConfirmForm() {
  const { ready, authenticated, confirmSignup, resendConfirmation } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefilledEmail = searchParams.get("email") ?? "";

  const [email, setEmail] = useState(prefilledEmail);
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  useEffect(() => {
    if (ready && authenticated) router.replace("/dashboard");
  }, [ready, authenticated, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setInfo(null);
    setSubmitting(true);
    try {
      await confirmSignup({ email, code });
      router.replace(`/login?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Confirmation failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function onResend() {
    if (!email) {
      setFormError("Enter your email to resend the code");
      return;
    }
    setFormError(null);
    setInfo(null);
    setResending(true);
    try {
      await resendConfirmation(email);
      setInfo("A new confirmation code was sent to your email.");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not resend code");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
        Confirm your email
      </h1>
      <p className="mt-1.5 text-sm text-ink-500">
        We sent a confirmation code to your inbox. Enter it below to activate
        your account.
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
          <label className="block text-sm font-medium text-ink-700" htmlFor="code">
            Confirmation code
          </label>
          <input
            id="code"
            type="text"
            required
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => setCode(e.target.value.trim())}
            className="input mt-1.5 w-full tracking-widest"
            placeholder="123456"
          />
        </div>

        {formError && (
          <p className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-600">
            {formError}
          </p>
        )}
        {info && (
          <p className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-700">
            {info}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || !ready}
          className="btn-primary w-full !rounded-lg justify-center disabled:opacity-60"
        >
          {submitting ? "Confirming…" : "Confirm account"}
        </button>

        <button
          type="button"
          onClick={onResend}
          disabled={resending}
          className="block w-full text-center text-sm font-semibold text-brand-600 hover:underline disabled:opacity-60"
        >
          {resending ? "Sending…" : "Resend confirmation code"}
        </button>

        <p className="text-center text-sm text-ink-500">
          Already confirmed?{" "}
          <Link
            href="/login"
            className="font-semibold text-brand-600 hover:underline"
          >
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}

export default function ConfirmPage() {
  return (
    <>
      <section className="flex flex-1 items-center justify-center">
        <Suspense fallback={<div className="w-full max-w-sm" />}>
          <ConfirmForm />
        </Suspense>
      </section>

      <AuthArtwork variant="signup" />
    </>
  );
}
