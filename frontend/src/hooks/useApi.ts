import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client.ts";

export interface ApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

interface Result<T> {
  key: string;
  data: T | null;
  error: ApiError | null;
}

/**
 * Load data on mount and whenever `deps` change (primitives only); `reload()` refetches.
 * Stale requests are aborted. While a refetch is running the previous data stays available.
 */
export function useApi<T>(load: (signal: AbortSignal) => Promise<T>, deps: unknown[]): ApiState<T> {
  const [tick, setTick] = useState(0);
  const [result, setResult] = useState<Result<T>>({ key: "", data: null, error: null });
  const key = JSON.stringify([...deps, tick]);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal)
      .then((data) => setResult({ key, data, error: null }))
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setResult((prev) => ({ key, data: prev.data, error: err instanceof ApiError ? err : new ApiError(String(err), 0) }));
      });
    return () => controller.abort();
    // `load` is recreated every render; `key` already captures what should trigger a refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data: result.data, error: result.error, loading: result.key !== key, reload };
}
