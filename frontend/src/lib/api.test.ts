import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  assetUrl,
  examQueryString,
  getExam,
  getStats,
  listExams,
  toApiError,
} from "./api";

function mockFetch(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("examQueryString", () => {
  it("includes filters, paging and sorting", () => {
    const query = examQueryString({
      split: "independent_test",
      label: "suspect",
      laterality: "OD",
      page: 2,
      sort: "min_thickness",
      order: "desc",
    });
    expect(Object.fromEntries(new URLSearchParams(query))).toEqual({
      split: "independent_test",
      label: "suspect",
      laterality: "OD",
      page: "2",
      page_size: "24",
      sort: "min_thickness",
      order: "desc",
    });
  });

  it("leaves out missing filters", () => {
    const params = new URLSearchParams(examQueryString({ page: 1, sort: "case", order: "asc" }));
    expect(params.has("split")).toBe(false);
    expect(params.has("label")).toBe(false);
    expect(params.has("laterality")).toBe(false);
  });
});

describe("requests", () => {
  it("lists exams from the API", async () => {
    const fetchMock = mockFetch({ ok: true, json: async () => ({ total: 0, items: [] }) });
    const page = await listExams({ page: 1, sort: "case", order: "asc" });
    expect(page.total).toBe(0);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/exams?");
  });

  it("encodes the exam path segments", async () => {
    const fetchMock = mockFetch({ ok: true, json: async () => ({}) });
    await getExam("train_validation", "normal", "1/../2");
    expect(String(fetchMock.mock.calls[0][0])).toContain(
      "/api/exams/train_validation/normal/1%2F..%2F2",
    );
  });

  it("passes the split to the statistics endpoint", async () => {
    const fetchMock = mockFetch({ ok: true, json: async () => ({ classes: [] }) });
    await getStats("independent_test");
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/api\/stats\?split=independent_test$/);
    await getStats(undefined);
    expect(String(fetchMock.mock.calls[1][0])).toMatch(/\/api\/stats$/);
  });

  it("turns an error response into an ApiError with the server detail", async () => {
    mockFetch({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      json: async () => ({ detail: "Exam index not available." }),
    });
    await expect(getStats(undefined)).rejects.toMatchObject({
      status: 503,
      message: "Exam index not available.",
    });
  });

  it("falls back to the status text when the body has no detail", async () => {
    mockFetch({
      ok: false,
      status: 500,
      statusText: "Server Error",
      json: async () => {
        throw new Error("not json");
      },
    });
    await expect(getStats(undefined)).rejects.toMatchObject({
      status: 500,
      message: "Server Error",
    });
  });

  it("reports an unreachable API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(getStats(undefined)).rejects.toMatchObject({
      status: 0,
      message: expect.stringContaining("Cannot reach the API"),
    });
  });

  it("lets aborts through unchanged", async () => {
    const abort = new DOMException("aborted", "AbortError");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(abort));
    await expect(getStats(undefined)).rejects.toBe(abort);
  });
});

describe("helpers", () => {
  it("builds asset URLs from the API base", () => {
    expect(assetUrl("/api/x")).toMatch(/\/api\/x$/);
  });

  it("wraps unknown errors", () => {
    expect(toApiError(new Error("boom"))).toMatchObject({ status: 0, message: "boom" });
    expect(toApiError("text")).toMatchObject({ status: 0, message: "Unexpected error" });
    const original = new ApiError(404, "no");
    expect(toApiError(original)).toBe(original);
  });
});
