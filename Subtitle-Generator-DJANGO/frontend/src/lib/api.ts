"use client";

// Single source of truth for the backend URL. The frontend never talks to
// Cognito directly; it only calls these backend endpoints.
export const apiUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const STORAGE_KEYS = {
  accessToken: "subly.access_token",
  idToken: "subly.id_token",
  refreshToken: "subly.refresh_token",
} as const;

export type TokenBundle = {
  access_token: string;
  id_token?: string | null;
  refresh_token?: string | null;
  expires_in?: number | null;
  refresh_expires_in?: number | null;
  token_type?: string;
};

export type MeResponse = {
  sub: string;
  username?: string | null;
  email?: string | null;
  name?: string | null;
  given_name?: string | null;
  family_name?: string | null;
  email_verified?: boolean | null;
  roles?: string[];
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function parseError(res: Response): Promise<string> {
  const text = await res.text();
  if (!text) return res.statusText;
  try {
    const json = JSON.parse(text);
    if (typeof json.detail === "string") return json.detail;
    if (Array.isArray(json.detail) && json.detail.length > 0) {
      return json.detail[0]?.msg ?? text;
    }
  } catch {
    /* ignore */
  }
  return text;
}

async function request<T>(
  path: string,
  init: RequestInit & { auth?: string | null } = {},
): Promise<T> {
  const { auth, ...rest } = init;
  const headers = new Headers(rest.headers);
  if (!headers.has("Content-Type") && rest.body) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    headers.set("Authorization", `Bearer ${auth}`);
  }
  const res = await fetch(`${apiUrl}${path}`, { ...rest, headers });
  if (!res.ok) {
    throw new ApiError(res.status, await parseError(res));
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  if (!ct.includes("application/json")) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  register(body: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) {
    return request<{ ok: boolean; message: string; confirmed?: boolean | null }>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },
  confirm(body: { email: string; code: string }) {
    return request<{ ok: boolean; confirmed: boolean; message: string }>(
      "/auth/confirm",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },
  resendConfirmation(body: { email: string }) {
    return request<{ ok: boolean; message: string }>(
      "/auth/resend-confirmation",
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },
  forgotPassword(body: { email: string }) {
    return request<{ ok: boolean; message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  resetPassword(body: { email: string; code: string; new_password: string }) {
    return request<{ ok: boolean; message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  login(body: { email: string; password: string }) {
    return request<TokenBundle>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  logout(refresh_token: string) {
    return request<{ ok: boolean }>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    });
  },
  me(accessToken: string) {
    return request<MeResponse>("/auth/me", { auth: accessToken });
  },
  health() {
    return request<{ status: string }>("/health");
  },
  listProjects(accessToken: string) {
    return request<ProjectSummary[]>("/api/v1/projects", { auth: accessToken });
  },
  getProject(accessToken: string, id: string) {
    return request<ProjectSummary>(`/api/v1/projects/${id}`, { auth: accessToken });
  },
  getProjectSrtUrl(accessToken: string, id: string) {
    return request<{ url: string }>(`/api/v1/projects/${id}/srt`, { auth: accessToken });
  },
  // Fetch the raw SRT text by first asking the backend for a presigned URL
  // and then GETting it from S3. Used by the inline subtitle viewer.
  async getProjectSrtContent(accessToken: string, id: string): Promise<string> {
    const { url } = await request<{ url: string }>(
      `/api/v1/projects/${id}/srt`,
      { auth: accessToken },
    );
    const res = await fetch(url);
    if (!res.ok) {
      throw new ApiError(res.status, `Failed to fetch SRT body: ${res.statusText}`);
    }
    return await res.text();
  },
  deleteProject(accessToken: string, id: string) {
    return request<void>(`/api/v1/projects/${id}`, {
      method: "DELETE",
      auth: accessToken,
    });
  },
  async uploadProject(
    accessToken: string,
    file: File,
    language: string | null,
  ): Promise<ProjectCreateResponse> {
    const form = new FormData();
    form.append("file", file);
    if (language) form.append("language", language);
    const res = await fetch(`${apiUrl}/api/v1/projects`, {
      method: "POST",
      body: form,
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!res.ok) {
      throw new ApiError(res.status, await parseError(res));
    }
    return (await res.json()) as ProjectCreateResponse;
  },
};

export type ProjectStatus =
  | "PENDING"
  | "QUEUED"
  | "TRANSCRIBING"
  | "COMPLETED"
  | "FAILED";

export type ProjectSummary = {
  id: string;
  original_filename: string;
  language: string | null;
  status: ProjectStatus;
  progress: number;
  error: string | null;
  has_srt: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type ProjectCreateResponse = {
  id: string;
  status: ProjectStatus;
};
