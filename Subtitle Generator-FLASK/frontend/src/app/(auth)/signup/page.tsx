"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthArtwork } from "@/components/AuthArtwork";
import { useAuth } from "@/components/AuthProvider";

export default function SignupPage() {
  const { ready, authenticated, register } = useAuth();
  const router = useRouter();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
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
      const { confirmed } = await register({
        email,
        password,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      });
      if (confirmed) {
        router.replace("/dashboard");
      } else {
        const params = new URLSearchParams({ email });
        router.replace(`/confirm?${params.toString()}`);
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <section className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-sm">
          <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
            Create your account
          </h1>
          <p className="mt-1.5 text-sm text-ink-500">
            Start generating subtitles in minutes.
          </p>

          <form onSubmit={onSubmit} className="mt-7 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  className="block text-sm font-medium text-ink-700"
                  htmlFor="firstName"
                >
                  First name
                </label>
                <input
                  id="firstName"
                  type="text"
                  autoComplete="given-name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="input mt-1.5 w-full"
                />
              </div>
              <div>
                <label
                  className="block text-sm font-medium text-ink-700"
                  htmlFor="lastName"
                >
                  Last name
                </label>
                <input
                  id="lastName"
                  type="text"
                  autoComplete="family-name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="input mt-1.5 w-full"
                />
              </div>
            </div>
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
              <label className="block text-sm font-medium text-ink-700" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1.5 w-full"
                placeholder="At least 6 characters"
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
              {submitting ? "Creating account…" : "Sign up"}
            </button>

            <p className="text-center text-sm text-ink-500">
              Already have an account?{" "}
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

      <AuthArtwork variant="signup" />
    </>
  );
}
