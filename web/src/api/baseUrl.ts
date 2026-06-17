/** Resolve API base URL — empty string means same-origin (Olares ingress / nginx proxy). */
export function resolveApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_URL as string | undefined;
  if (raw === "" || raw === "/") {
    return "";
  }
  return (raw ?? "http://localhost:8000").replace(/\/+$/, "");
}

export function resolveWebSocketBaseUrl(): string {
  const httpBase = resolveApiBaseUrl();
  if (!httpBase) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }
  return httpBase.replace(/^http/i, "ws");
}
