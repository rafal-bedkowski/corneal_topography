import type { ExamDetail, ExamPage, ExamQuery, Split, StatsResponse } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const PAGE_SIZE = 24;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function toApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, error instanceof Error ? error.message : "Unexpected error");
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "Cannot reach the API. Check that the backend is running.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }
  return (await response.json()) as T;
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const { detail } = body as { detail: unknown };
      if (typeof detail === "string") return detail;
    }
  } catch {
    // The response had no JSON body; fall through to the status text.
  }
  return response.statusText || `Request failed (${response.status})`;
}

export function assetUrl(path: string): string {
  return `${API_URL}${path}`;
}

export function examQueryString(query: ExamQuery): string {
  const params = new URLSearchParams();
  if (query.split) params.set("split", query.split);
  if (query.label) params.set("label", query.label);
  if (query.laterality) params.set("laterality", query.laterality);
  params.set("page", String(query.page));
  params.set("page_size", String(PAGE_SIZE));
  params.set("sort", query.sort);
  params.set("order", query.order);
  return params.toString();
}

export function listExams(query: ExamQuery, signal?: AbortSignal): Promise<ExamPage> {
  return getJson<ExamPage>(`/api/exams?${examQueryString(query)}`, signal);
}

export function getExam(
  split: string,
  label: string,
  caseNumber: string,
  signal?: AbortSignal,
): Promise<ExamDetail> {
  const path = [split, label, caseNumber].map(encodeURIComponent).join("/");
  return getJson<ExamDetail>(`/api/exams/${path}`, signal);
}

export function getStats(split: Split | undefined, signal?: AbortSignal): Promise<StatsResponse> {
  const query = split ? `?split=${split}` : "";
  return getJson<StatsResponse>(`/api/stats${query}`, signal);
}
