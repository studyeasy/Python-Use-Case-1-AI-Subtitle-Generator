"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api, ApiError, STORAGE_KEYS, type MeResponse } from "@/lib/api";

type Profile = {
  username?: string;
  email?: string;
  sub?: string;
};

type AuthState = {
  ready: boolean;
  authenticated: boolean;
  token: string | undefined;
  username: string | undefined;
  email: string | undefined;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (input: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) => Promise<{ confirmed: boolean }>;
  confirmSignup: (input: {
    email: string;
    code: string;
    password?: string;
  }) => Promise<void>;
  resendConfirmation: (email: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (input: {
    email: string;
    code: string;
    new_password: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  authFetch: (input: string, init?: RequestInit) => Promise<Response>;
};

const AuthContext = createContext<AuthState | null>(null);

function readToken(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function writeToken(key: string, value: string | null | undefined) {
  if (typeof window === "undefined") return;
  if (value) {
    window.localStorage.setItem(key, value);
  } else {
    window.localStorage.removeItem(key);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [profile, setProfile] = useState<Profile>({});
  const [error, setError] = useState<string | null>(null);

  const clearSession = useCallback(() => {
    writeToken(STORAGE_KEYS.accessToken, null);
    writeToken(STORAGE_KEYS.idToken, null);
    writeToken(STORAGE_KEYS.refreshToken, null);
    setToken(undefined);
    setProfile({});
  }, []);

  const hydrateProfile = useCallback(async (accessToken: string) => {
    try {
      const me: MeResponse = await api.me(accessToken);
      setProfile({
        username: me.username ?? me.email ?? undefined,
        email: me.email ?? undefined,
        sub: me.sub,
      });
      return true;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        return false;
      }
      // Network or transient error — keep the token but leave profile empty.
      return true;
    }
  }, []);

  useEffect(() => {
    const stored = readToken(STORAGE_KEYS.accessToken);
    if (!stored) {
      setReady(true);
      return;
    }
    setToken(stored);
    hydrateProfile(stored)
      .then((ok) => {
        if (!ok) clearSession();
      })
      .finally(() => setReady(true));
  }, [hydrateProfile, clearSession]);

  const login = useCallback<AuthState["login"]>(
    async (email, password) => {
      setError(null);
      try {
        const tokens = await api.login({ email, password });
        writeToken(STORAGE_KEYS.accessToken, tokens.access_token);
        writeToken(STORAGE_KEYS.idToken, tokens.id_token ?? null);
        writeToken(STORAGE_KEYS.refreshToken, tokens.refresh_token ?? null);
        setToken(tokens.access_token);
        await hydrateProfile(tokens.access_token);
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Login failed";
        setError(message);
        throw err;
      }
    },
    [hydrateProfile],
  );

  const register = useCallback<AuthState["register"]>(
    async (input) => {
      setError(null);
      try {
        const result = await api.register(input);
        const confirmed = result.confirmed !== false;
        if (confirmed) {
          await login(input.email, input.password);
        }
        return { confirmed };
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Registration failed";
        setError(message);
        throw err;
      }
    },
    [login],
  );

  const confirmSignup = useCallback<AuthState["confirmSignup"]>(
    async ({ email, code, password }) => {
      setError(null);
      try {
        await api.confirm({ email, code });
        if (password) {
          await login(email, password);
        }
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Confirmation failed";
        setError(message);
        throw err;
      }
    },
    [login],
  );

  const resendConfirmation = useCallback<AuthState["resendConfirmation"]>(
    async (email) => {
      setError(null);
      try {
        await api.resendConfirmation({ email });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Could not resend code";
        setError(message);
        throw err;
      }
    },
    [],
  );

  const forgotPassword = useCallback<AuthState["forgotPassword"]>(
    async (email) => {
      setError(null);
      try {
        await api.forgotPassword({ email });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Could not start password reset";
        setError(message);
        throw err;
      }
    },
    [],
  );

  const resetPassword = useCallback<AuthState["resetPassword"]>(
    async ({ email, code, new_password }) => {
      setError(null);
      try {
        await api.resetPassword({ email, code, new_password });
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Could not reset password";
        setError(message);
        throw err;
      }
    },
    [],
  );

  const logout = useCallback<AuthState["logout"]>(async () => {
    const refresh = readToken(STORAGE_KEYS.refreshToken);
    try {
      if (refresh) await api.logout(refresh);
    } catch {
      /* ignore — logout is best-effort */
    }
    clearSession();
  }, [clearSession]);

  const authFetch = useCallback<AuthState["authFetch"]>(
    async (input, init = {}) => {
      const accessToken = readToken(STORAGE_KEYS.accessToken) ?? token;
      const url = input.startsWith("http")
        ? input
        : `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}${input}`;
      const headers = new Headers(init.headers);
      if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
      return fetch(url, { ...init, headers });
    },
    [token],
  );

  const value = useMemo<AuthState>(
    () => ({
      ready,
      authenticated: !!token,
      token,
      username: profile.username,
      email: profile.email,
      error,
      login,
      register,
      confirmSignup,
      resendConfirmation,
      forgotPassword,
      resetPassword,
      logout,
      authFetch,
    }),
    [
      ready,
      token,
      profile,
      error,
      login,
      register,
      confirmSignup,
      resendConfirmation,
      forgotPassword,
      resetPassword,
      logout,
      authFetch,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
