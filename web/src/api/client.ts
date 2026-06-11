/**
 * Single backend gateway (Sprint 0 plan §4.6 / §4.7 / coding-standards.md §157).
 *
 * Every request flows through `request()` which attaches `Authorization: Bearer
 * <token>` from `localStorage`. A 401 clears the token and bounces to `/login`,
 * satisfying "unauthenticated requests redirect to /login". Components import the
 * typed endpoint helpers below and never call `fetch()` directly.
 */

import type {
  AssetVersion,
  IdeaCreateBody,
  PipelineApproveResponse,
  PipelineRegenerateResponse,
  PipelineStartResponse,
  PipelineStatus,
  Project,
} from "./types";

const TOKEN_KEY = "aimpos.token";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function redirectToLogin(): void {
  // Guard against a reload loop while already on the login screen (e.g. during
  // token validation). A hard navigation is fine for the MVP.
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

async function extractDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Non-JSON or empty body — fall through to a generic message.
  }
  return `Request failed with status ${response.status}`;
}

async function requestRaw(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    clearToken();
    redirectToLogin();
    throw new ApiError(401, "Unauthorized");
  }

  if (!response.ok) {
    throw new ApiError(response.status, await extractDetail(response));
  }

  return response;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await requestRaw(path, init);
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function requestText(path: string, init: RequestInit = {}): Promise<string> {
  const response = await requestRaw(path, init);
  return response.text();
}

async function requestBlob(path: string, init: RequestInit = {}): Promise<Blob> {
  const response = await requestRaw(path, init);
  return response.blob();
}

// --- Typed endpoint helpers ------------------------------------------------

export function listProjects(): Promise<Project[]> {
  return request<Project[]>("/projects");
}

export function getPipelineStatus(projectId: string): Promise<PipelineStatus> {
  return request<PipelineStatus>(`/pipeline/status?project_id=${encodeURIComponent(projectId)}`);
}

export function startPipeline(projectId: string): Promise<PipelineStartResponse> {
  return request<PipelineStartResponse>("/pipeline/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
}

export interface PipelineApproveBody {
  project_id: string;
  stage: string;
  decision: "GRANT" | "REJECT" | "APPROVED" | "REJECTED";
  note?: string;
}

export function approvePipeline(body: PipelineApproveBody): Promise<PipelineApproveResponse> {
  return request<PipelineApproveResponse>("/pipeline/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function regeneratePipeline(body: {
  project_id: string;
  stage: string;
}): Promise<PipelineRegenerateResponse> {
  return request<PipelineRegenerateResponse>("/pipeline/regenerate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function submitIdea(body: IdeaCreateBody): Promise<AssetVersion> {
  return request<AssetVersion>("/ideas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listAssets(projectId: string): Promise<AssetVersion[]> {
  return request<AssetVersion[]>(`/assets?project_id=${encodeURIComponent(projectId)}`);
}

export function getAssetContent(assetId: string): Promise<string> {
  return requestText(`/assets/${encodeURIComponent(assetId)}/content`, {
    headers: { Accept: "text/markdown, text/plain" },
  });
}

export function getAssetContentBlob(assetId: string): Promise<Blob> {
  return requestBlob(`/assets/${encodeURIComponent(assetId)}/content`, {
    headers: { Accept: "image/png" },
  });
}

export function updateAssetText(assetId: string, text: string): Promise<AssetVersion> {
  return request<AssetVersion>(`/assets/${encodeURIComponent(assetId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function uploadAsset(projectId: string, stage: string, file: File): Promise<AssetVersion> {
  const form = new FormData();
  form.append("project_id", projectId);
  form.append("stage", stage);
  form.append("file", file);
  return request<AssetVersion>("/assets", { method: "POST", body: form });
}
