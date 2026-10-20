import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { useApi } from "./useApi";

describe("useApi", () => {
  it("starts loading and then exposes the data", async () => {
    const load = vi.fn().mockResolvedValue("hello");
    const { result } = renderHook(() => useApi("a", load));
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe("hello");
    expect(result.current.error).toBeNull();
  });

  it("exposes API errors", async () => {
    const load = vi.fn().mockRejectedValue(new ApiError(503, "down"));
    const { result } = renderHook(() => useApi("a", load));
    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error?.status).toBe(503);
    expect(result.current.data).toBeNull();
  });

  it("wraps non-API errors", async () => {
    const load = vi.fn().mockRejectedValue(new Error("boom"));
    const { result } = renderHook(() => useApi("a", load));
    await waitFor(() => expect(result.current.error?.message).toBe("boom"));
  });

  it("reloads on demand", async () => {
    const load = vi.fn().mockResolvedValueOnce("first").mockResolvedValueOnce("second");
    const { result } = renderHook(() => useApi("a", load));
    await waitFor(() => expect(result.current.data).toBe("first"));
    act(() => result.current.reload());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.data).toBe("second"));
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("loads again and reports loading when the key changes", async () => {
    const load = vi.fn((signal: AbortSignal) => {
      void signal;
      return Promise.resolve(Math.random());
    });
    const { result, rerender } = renderHook(({ id }) => useApi(id, load), {
      initialProps: { id: "a" },
    });
    await waitFor(() => expect(result.current.loading).toBe(false));
    rerender({ id: "b" });
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("aborts the previous request when the key changes", async () => {
    const signals: AbortSignal[] = [];
    const load = vi.fn((signal: AbortSignal) => {
      signals.push(signal);
      return new Promise<string>(() => undefined);
    });
    const { rerender } = renderHook(({ id }) => useApi(id, load), { initialProps: { id: "a" } });
    rerender({ id: "b" });
    expect(signals[0].aborted).toBe(true);
    expect(signals[1].aborted).toBe(false);
  });

  it("ignores the result of an aborted request", async () => {
    let rejectFirst: (error: unknown) => void = () => undefined;
    const load = vi
      .fn()
      .mockImplementationOnce(() => new Promise((_, reject) => (rejectFirst = reject)))
      .mockResolvedValueOnce("fresh");
    const { result, rerender } = renderHook(({ id }) => useApi(id, load), {
      initialProps: { id: "a" },
    });
    rerender({ id: "b" });
    rejectFirst(new DOMException("aborted", "AbortError"));
    await waitFor(() => expect(result.current.data).toBe("fresh"));
    expect(result.current.error).toBeNull();
  });
});
