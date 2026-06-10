"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { MarketingHeader } from "@/components/MarketingHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/components/AuthProvider";
import { ChevronLeft, Eye } from "@/components/icons";
import { SrtViewer } from "@/components/SrtViewer";
import {
  api,
  ApiError,
  type ProjectStatus,
  type ProjectSummary,
} from "@/lib/api";

const TERMINAL = new Set<ProjectStatus>(["COMPLETED", "FAILED"]);

function statusLabel(status: ProjectStatus): string {
  switch (status) {
    case "PENDING":
      return "Waiting";
    case "QUEUED":
      return "Queued";
    case "TRANSCRIBING":
      return "Transcribing";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
  }
}

function statusToneClasses(status: ProjectStatus): string {
  if (status === "COMPLETED") return "bg-success-50 text-success-600";
  if (status === "FAILED") return "bg-danger-50 text-danger-600";
  return "bg-warning-50 text-warning-600";
}

function ProjectPageInner() {
  const params = useParams<{ id: string }>();
  const projectId = params?.id;
  const router = useRouter();
  const { token } = useAuth();
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchOnce = useCallback(async () => {
    if (!token || !projectId) return;
    try {
      const p = await api.getProject(token, projectId);
      setProject(p);
      setError(null);
      if (TERMINAL.has(p.status) && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to load project";
      setError(msg);
    }
  }, [token, projectId]);

  useEffect(() => {
    fetchOnce();
    pollRef.current = setInterval(fetchOnce, 2000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchOnce]);

  async function onDownload() {
    if (!token || !projectId) return;
    setDownloadError(null);
    try {
      const res = await api.getProjectSrtUrl(token, projectId);
      window.location.assign(res.url);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Could not get SRT URL";
      setDownloadError(msg);
    }
  }

  async function onDelete() {
    if (!token || !projectId) return;
    if (!window.confirm("Delete this project? This cannot be undone.")) return;
    setDeleteError(null);
    setDeleting(true);
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    try {
      await api.deleteProject(token, projectId);
      router.push("/dashboard");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to delete project";
      setDeleteError(msg);
      setDeleting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <MarketingHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <div className="card p-8">
          <div className="flex items-center justify-between gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1 text-sm font-medium text-ink-500 hover:text-ink-900"
            >
              <ChevronLeft className="h-4 w-4" />
              Back to dashboard
            </Link>
            {project && (
              <button
                type="button"
                onClick={onDelete}
                disabled={deleting}
                className="inline-flex items-center gap-1 rounded-md border border-danger-200 bg-white px-3 py-1.5 text-sm font-medium text-danger-600 hover:bg-danger-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete project"}
              </button>
            )}
          </div>
          {deleteError && (
            <p className="mt-3 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
              {deleteError}
            </p>
          )}

          {error && !project && (
            <p className="mt-6 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
              {error}
            </p>
          )}

          {project && (
            <>
              <div className="mt-2">
                <h1 className="truncate text-2xl font-extrabold tracking-tight text-ink-900">
                  {project.original_filename}
                </h1>
                <p className="mt-1 text-sm text-ink-500">
                  Project ID: <span className="font-mono">{project.id}</span>
                </p>
              </div>

              <div className="mt-6 flex items-center gap-3">
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusToneClasses(project.status)}`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                  {statusLabel(project.status)}
                </span>
                {project.status === "TRANSCRIBING" && (
                  <span className="text-xs text-ink-500">
                    {project.progress}%
                  </span>
                )}
              </div>

              <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-ink-100">
                <div
                  className={`h-full transition-all ${
                    project.status === "FAILED"
                      ? "bg-danger-600"
                      : project.status === "COMPLETED"
                      ? "bg-success-600"
                      : "bg-brand-500"
                  }`}
                  style={{
                    width: `${
                      project.status === "COMPLETED"
                        ? 100
                        : project.status === "FAILED"
                        ? 100
                        : project.progress
                    }%`,
                  }}
                />
              </div>

              {project.status === "FAILED" && project.error && (
                <p className="mt-4 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
                  {project.error}
                </p>
              )}

              {project.status === "COMPLETED" && (
                <div className="mt-6 flex flex-col items-start gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setViewerOpen(true)}
                      className="btn-secondary inline-flex items-center gap-2"
                    >
                      <Eye className="h-4 w-4" />
                      View SRT
                    </button>
                    <button
                      type="button"
                      onClick={onDownload}
                      className="btn-primary"
                    >
                      Download SRT
                    </button>
                  </div>
                  {downloadError && (
                    <p className="text-sm text-danger-600">{downloadError}</p>
                  )}
                </div>
              )}

              {!TERMINAL.has(project.status) && (
                <p className="mt-6 text-xs text-ink-500">
                  Live updates every 2 seconds…
                </p>
              )}
            </>
          )}
        </div>
      </main>
      <SrtViewer
        open={viewerOpen}
        projectId={projectId ?? null}
        filename={project?.original_filename ?? null}
        onClose={() => setViewerOpen(false)}
      />
    </div>
  );
}

export default function ProjectPage() {
  return (
    <RequireAuth>
      <ProjectPageInner />
    </RequireAuth>
  );
}
