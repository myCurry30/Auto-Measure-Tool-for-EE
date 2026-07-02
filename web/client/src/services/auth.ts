const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface LoginResponse {
  token: string;
  expires_at: string;
  role: string;
  display_name: string;
}

export async function login(username: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  if (res.status === 425) {
    // ARP not resolved, wait 2 seconds and retry
    await new Promise((r) => setTimeout(r, 2000));
    return login(username);
  }
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
}

export function logout(): void {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

export function getStoredUser(): {
  username: string;
  role: string;
  display_name: string;
} | null {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function setStoredUser(
  user: { username: string; role: string; display_name: string },
): void {
  localStorage.setItem("user", JSON.stringify(user));
}

/** Generic fetch wrapper that attaches the Bearer token automatically. */
export async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}
