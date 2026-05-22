import type { ApiErrorBody } from '../types/api';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody;

  constructor(status: number, body: ApiErrorBody) {
    const detail =
      typeof body.detail === 'string'
        ? body.detail
        : formatFieldErrors(body);
    super(detail || `Request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

function formatFieldErrors(body: ApiErrorBody): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(body)) {
    if (key === 'detail' || value === undefined) continue;
    const msg = Array.isArray(value) ? value.join(' ') : String(value);
    parts.push(`${key}: ${msg}`);
  }
  return parts.join('; ');
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function hasAccessToken(): boolean {
  return Boolean(getAccessToken());
}

type RequestOptions = RequestInit & {
  skipAuth?: boolean;
  skipRefresh?: boolean;
};

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const response = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    clearTokens();
    return null;
  }

  const data = (await response.json()) as { access: string };
  localStorage.setItem(ACCESS_KEY, data.access);
  return data.access;
}

async function getRefreshedAccess(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { skipAuth = false, skipRefresh = false, headers, ...init } = options;

  const requestHeaders = new Headers(headers);
  if (!requestHeaders.has('Content-Type') && init.body) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`);
    }
  }

  let response = await fetch(path, {
    ...init,
    headers: requestHeaders,
  });

  if (response.status === 401 && !skipAuth && !skipRefresh) {
    const newAccess = await getRefreshedAccess();
    if (newAccess) {
      requestHeaders.set('Authorization', `Bearer ${newAccess}`);
      response = await fetch(path, { ...init, headers: requestHeaders });
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const body = text ? (JSON.parse(text) as ApiErrorBody) : {};

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }

  return body as T;
}
