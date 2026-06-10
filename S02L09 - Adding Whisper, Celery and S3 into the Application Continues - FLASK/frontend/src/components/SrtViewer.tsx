"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { formatDuration, parseSrt, type SrtCue } from "@/lib/srt";
import { useAuth } from "@/components/AuthProvider";

type Props = {
  open: boolean;
  projectId: string | null;
  filename?: string | null;
  onClose: () => void;
};

// Modal that fetches a project's SRT and renders the parsed cues inline.
// Plain SRT text is preserved on a "Raw" tab so users can copy it.
export function SrtViewer({ open, projectId, filename, onClose }: Props) {
  const { token } = useAuth();
  const [raw, setRaw] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"cues" | "raw">("cues");

  useEffect(() => {
    if (!open || !projectId || !token) return;
    let cancelled = false;
    setRaw(null);
    setError(null);
    setLoading(true);
    setTab("cues");
    api
      .getProjectSrtContent(token, projectId)
      .then((text) => {
        if (!cancelled) setRaw(text);
      })
      .catch((err) => {
        if (cancelled) return;
        const msg =
          err instanceof ApiError ? err.message : "Failed to load subtitles";
        setError(msg);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, projectId, token]);

  // Close on Escape.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const cues: SrtCue[] = useMemo(() => (raw ? parseSrt(raw) : []), [raw]);
  const lastEndMs = cues.length ? cues[cues.length - 1].endMs : 0;

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="View subtitles"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between border-b border-ink-100 px-6 py-4">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-bold text-ink-900">
              Subtitles
            </h2>
            <p className="mt-0.5 truncate text-xs text-ink-500">
              {filename ?? projectId}
              {cues.length > 0 && (
                <>
                  {" · "}
                  {cues.length} cue{cues.length === 1 ? "" : "s"}
                  {" · "}
                  {formatDuration(lastEndMs)}
                </>
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="ml-3 rounded-md p-1.5 text-ink-500 hover:bg-ink-50 hover:text-ink-900"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
              aria-hidden
            >
              <path d="M18 6 6 18" />
              <path d="M6 6l12 12" />
            </svg>
          </button>
        </header>

        <div className="border-b border-ink-100 px-6">
          <div className="flex gap-4 text-sm">
            <TabButton active={tab === "cues"} onClick={() => setTab("cues")}>
              Cues
            </TabButton>
            <TabButton active={tab === "raw"} onClick={() => setTab("raw")}>
              Raw SRT
            </TabButton>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-6 py-4">
          {loading && (
            <p className="text-sm text-ink-500">Loading subtitles…</p>
          )}
          {error && !loading && (
            <p className="rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
              {error}
            </p>
          )}
          {!loading && !error && raw && tab === "cues" && (
            cues.length === 0 ? (
              <p className="text-sm text-ink-500">No cues parsed from this file.</p>
            ) : (
              <ol className="space-y-3">
                {cues.map((cue) => (
                  <li
                    key={cue.index}
                    className="rounded-lg border border-ink-100 bg-white p-3"
                  >
                    <div className="flex items-center justify-between gap-3 text-xs font-mono text-ink-500">
                      <span>#{cue.index}</span>
                      <span>
                        {cue.startLabel} → {cue.endLabel}
                      </span>
                    </div>
                    <p className="mt-1.5 whitespace-pre-wrap text-sm text-ink-900">
                      {cue.text}
                    </p>
                  </li>
                ))}
              </ol>
            )
          )}
          {!loading && !error && raw && tab === "raw" && (
            <pre className="whitespace-pre-wrap break-words rounded-lg bg-ink-50 p-3 font-mono text-xs text-ink-900">
              {raw}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px border-b-2 px-1 py-3 text-sm font-medium transition ${
        active
          ? "border-brand-600 text-ink-900"
          : "border-transparent text-ink-500 hover:text-ink-900"
      }`}
    >
      {children}
    </button>
  );
}
