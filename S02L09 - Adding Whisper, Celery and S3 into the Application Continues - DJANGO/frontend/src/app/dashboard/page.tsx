"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
} from "@/components/icons";
import { ProjectRowMenu } from "@/components/ProjectRowMenu";
import { SrtViewer } from "@/components/SrtViewer";
import {
  api,
  ApiError,
  type ProjectStatus,
  type ProjectSummary,
} from "@/lib/api";

type DisplayStatus = "Completed" | "Processing" | "Failed";

function toDisplayStatus(s: ProjectStatus): DisplayStatus {
  if (s === "COMPLETED") return "Completed";
  if (s === "FAILED") return "Failed";
  return "Processing";
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function DashboardPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [viewing, setViewing] = useState<{ id: string; filename: string } | null>(
    null,
  );
  const hasActive = useRef(false);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const data = await api.listProjects(token);
      setProjects(data);
      hasActive.current = data.some(
        (p) => p.status !== "COMPLETED" && p.status !== "FAILED",
      );
      setError(null);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to load projects";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    load();
    const id = setInterval(() => {
      if (hasActive.current) load();
    }, 3000);
    return () => clearInterval(id);
  }, [token, load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return projects;
    return projects.filter((p) =>
      p.original_filename.toLowerCase().includes(q),
    );
  }, [projects, query]);

  async function onDeleteProject(p: ProjectSummary) {
    if (!token) return;
    if (!window.confirm(`Delete "${p.original_filename}"? This cannot be undone.`))
      return;
    setActionError(null);
    setDeletingId(p.id);
    try {
      await api.deleteProject(token, p.id);
      setProjects((prev) => prev.filter((x) => x.id !== p.id));
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to delete project";
      setActionError(msg);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">
            My Projects
          </h1>
          <p className="mt-1 text-sm text-ink-500">
            Manage and view your subtitle projects.
          </p>
        </div>
        <Link href="/new-project" className="btn-primary">
          <Plus className="h-4 w-4" />
          New Project
        </Link>
      </header>

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-72">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects..."
            className="input pl-10"
          />
        </div>
        <Filter label="All Status" />
        <Filter label="All Files" />
      </div>

      {error && (
        <p className="mt-4 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
          {error}
        </p>
      )}
      {actionError && (
        <p className="mt-4 rounded-md bg-danger-50 px-3 py-2 text-sm text-danger-600">
          {actionError}
        </p>
      )}

      <div className="mt-6 overflow-hidden rounded-2xl border border-ink-200">
        <table className="w-full text-sm">
          <thead className="bg-ink-50 text-left text-xs font-semibold uppercase tracking-wider text-ink-500">
            <tr>
              <th className="px-5 py-3">Project</th>
              <th className="px-5 py-3">Language</th>
              <th className="px-5 py-3">Progress</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Created</th>
              <th className="w-10 px-5 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100 bg-white">
            {loading && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-ink-500">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-ink-500">
                  No projects yet.{" "}
                  <Link href="/new-project" className="text-brand-600 underline">
                    Create your first one
                  </Link>
                  .
                </td>
              </tr>
            )}
            {filtered.map((p) => (
              <tr
                key={p.id}
                onClick={() => router.push(`/projects/${p.id}`)}
                className="cursor-pointer hover:bg-ink-50/60"
              >
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="grid h-9 w-12 place-items-center rounded-md bg-gradient-to-br from-brand-200 to-brand-500" />
                    <span className="truncate font-medium text-ink-900">
                      {p.original_filename}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-4 text-ink-500">
                  {p.language ?? "auto"}
                </td>
                <td className="px-5 py-4 text-ink-500">
                  {p.status === "COMPLETED" ? "100%" : `${p.progress}%`}
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={toDisplayStatus(p.status)} />
                </td>
                <td className="px-5 py-4 text-ink-500">
                  {formatDate(p.created_at)}
                </td>
                <td className="px-5 py-4">
                  <ProjectRowMenu
                    hasSrt={p.has_srt}
                    busy={deletingId === p.id}
                    onViewSrt={() =>
                      setViewing({ id: p.id, filename: p.original_filename })
                    }
                    onDelete={() => onDeleteProject(p)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-5 flex items-center justify-between text-sm text-ink-500">
        <span>
          {filtered.length} project{filtered.length === 1 ? "" : "s"}
        </span>
        <Pagination />
      </div>

      <SrtViewer
        open={viewing !== null}
        projectId={viewing?.id ?? null}
        filename={viewing?.filename}
        onClose={() => setViewing(null)}
      />
    </div>
  );
}

function Filter({ label }: { label: string }) {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-2 rounded-lg border border-ink-200 bg-white px-3.5 py-2.5 text-sm font-medium text-ink-700 hover:bg-ink-50"
    >
      {label}
      <ChevronDown className="h-4 w-4" />
    </button>
  );
}

function StatusBadge({ status }: { status: DisplayStatus }) {
  const styles: Record<DisplayStatus, string> = {
    Completed: "bg-success-50 text-success-600",
    Processing: "bg-warning-50 text-warning-600",
    Failed: "bg-danger-50 text-danger-600",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

function Pagination() {
  return (
    <div className="flex items-center gap-1">
      <PageBtn aria-label="Previous">
        <ChevronLeft className="h-4 w-4" />
      </PageBtn>
      <PageBtn active>1</PageBtn>
      <PageBtn aria-label="Next">
        <ChevronRight className="h-4 w-4" />
      </PageBtn>
    </div>
  );
}

function PageBtn({
  active,
  children,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      {...rest}
      className={`grid h-8 w-8 place-items-center rounded-md border text-xs font-medium ${
        active
          ? "border-brand-600 bg-brand-600 text-white"
          : "border-ink-200 bg-white text-ink-700 hover:bg-ink-50"
      }`}
    >
      {children}
    </button>
  );
}
