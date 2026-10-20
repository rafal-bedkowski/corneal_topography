"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { type ApiError, toApiError } from "@/lib/api";

interface Settled<T> {
  key: string;
  attempt: number;
  data: T | null;
  error: ApiError | null;
}

export interface ApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

/**
 * Runs `load` whenever `key` changes (or `reload` is called) and exposes its outcome.
 * `key` must identify everything `load` depends on.
 */
export function useApi<T>(key: string, load: (signal: AbortSignal) => Promise<T>): ApiState<T> {
  const [attempt, setAttempt] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const run = useEffectEvent(load);

  useEffect(() => {
    const controller = new AbortController();
    run(controller.signal).then(
      (data) => setSettled({ key, attempt, data, error: null }),
      (error: unknown) => {
        if (controller.signal.aborted) return;
        setSettled({ key, attempt, data: null, error: toApiError(error) });
      },
    );
    return () => controller.abort();
  }, [key, attempt]);

  const current = settled !== null && settled.key === key && settled.attempt === attempt;
  return {
    data: current ? settled.data : null,
    error: current ? settled.error : null,
    loading: !current,
    reload: () => setAttempt((value) => value + 1),
  };
}
