/**
 * Bootstrap HTTP wrapper.
 *
 * The architecture target (CLAUDE.md Rule 5 §4) is that this file is replaced
 * once `npm run openapi:gen` produces `src/api/generated/client.ts`.
 * Until then this thin wrapper carries the JWT interceptor and silent refresh
 * so the SPA can boot on a fresh checkout.
 */
import { useAuthStore } from '@/store/auth';

export type ApiEnvelope<T> = {
  code: number;
  message: string;
  data: T | null;
};

let refreshing: Promise<void> | null = null;

async function refreshIfNeeded() {
  const auth = useAuthStore();
  if (!auth.refreshToken) return;
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: auth.refreshToken }),
        });
        if (!res.ok) throw new Error('refresh failed');
        const env = (await res.json()) as ApiEnvelope<{ access_token: string }>;
        if (env.code === 0 && env.data?.access_token) {
          auth.setAccessToken(env.data.access_token);
        } else {
          auth.clear();
        }
      } catch {
        auth.clear();
      } finally {
        refreshing = null;
      }
    })();
  }
  await refreshing;
}

async function request<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const auth = useAuthStore();
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json');
  if (auth.accessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${auth.accessToken}`);
  }
  const res = await fetch(path, { ...init, headers });
  if (res.status === 401 && !retried && auth.refreshToken && !path.endsWith('/auth/refresh')) {
    await refreshIfNeeded();
    return request<T>(path, init, true);
  }
  const json = await res.json().catch(() => ({}));
  const env = json as ApiEnvelope<T>;
  if (!res.ok || env.code !== 0) {
    const errCode = (env.data as any)?.error_code ?? `HTTP_${res.status}`;
    const message = env.message ?? `Request failed (${res.status})`;
    const err = new Error(message) as Error & { code: string; status: number };
    err.code = errCode;
    err.status = res.status;
    throw err;
  }
  return env.data as T;
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(path, { ...(init ?? {}), method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
