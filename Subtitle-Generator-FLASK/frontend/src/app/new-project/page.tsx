"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { MarketingHeader } from "@/components/MarketingHeader";
import { ChevronDown, ChevronLeft, CloudUpload } from "@/components/icons";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";

const LANGUAGE_OPTIONS: { label: string; value: string | null }[] = [
  { label: "Auto-detect", value: null },
  { label: "English", value: "en" },
  { label: "Spanish", value: "es" },
  { label: "French", value: "fr" },
  { label: "German", value: "de" },
  { label: "Hindi", value: "hi" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const { token, ready, authenticated } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [languageIdx, setLanguageIdx] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function pickFile() {
    fileInputRef.current?.click();
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  async function onSubmit() {
    setError(null);
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    if (!token) {
      setError("You need to sign in before uploading.");
      return;
    }
    setSubmitting(true);
    try {
      const lang = LANGUAGE_OPTIONS[languageIdx]?.value ?? null;
      const project = await api.uploadProject(token, file, lang);
      router.push(`/projects/${project.id}`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Upload failed";
      setError(msg);
      setSubmitting(false);
    }
  }

  if (ready && !authenticated) {
    return (
      <div className="flex min-h-screen flex-col">
        <MarketingHeader />
        <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-10">
          <div className="card p-8 text-center">
            <p className="text-sm text-ink-700">
              Please <Link className="text-brand-600 underline" href="/login">sign in</Link> to start a project.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <MarketingHeader />

      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-10">
        <div className="card p-8">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1 text-sm font-medium text-ink-500 hover:text-ink-900"
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Link>

          <div className="mt-2 text-center">
            <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
              New Project
            </h1>
            <p className="mt-1 text-sm text-ink-500">
              Upload your file to generate subtitles.
            </p>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`mt-8 rounded-2xl border-2 border-dashed p-10 transition ${
              dragOver
                ? "border-brand-500 bg-brand-50"
                : "border-brand-300 bg-brand-50/50"
            }`}
          >
            <div className="flex flex-col items-center text-center">
              <CloudUpload className="h-9 w-9 text-ink-500" />
              <p className="mt-3 text-base font-semibold text-ink-900">
                {file ? file.name : "Drag & drop your file here"}
              </p>
              {!file && <p className="mt-1 text-xs text-ink-500">or</p>}
              <button
                type="button"
                onClick={pickFile}
                className="btn-primary mt-3"
              >
                {file ? "Choose Different File" : "Choose File"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*,video/*"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <p className="mt-4 text-xs text-ink-500">
                Supports MP4, MOV, MP3, WAV and more
              </p>
            </div>
          </div>

          <div className="mt-6">
            <label htmlFor="lang" className="label">
              Project Language
            </label>
            <div className="relative">
              <select
                id="lang"
                value={languageIdx}
                onChange={(e) => setLanguageIdx(Number(e.target.value))}
                className="input appearance-none pr-10"
              >
                {LANGUAGE_OPTIONS.map((opt, idx) => (
                  <option key={opt.label} value={idx}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-500" />
            </div>
          </div>

          {error && (
            <p className="mt-4 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={onSubmit}
            disabled={submitting || !file}
            className="btn-primary mt-6 w-full !rounded-xl disabled:opacity-60"
          >
            {submitting ? "Uploading…" : "Upload & Process"}
          </button>
        </div>
      </main>
    </div>
  );
}
