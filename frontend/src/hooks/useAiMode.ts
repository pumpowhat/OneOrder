import { useState, useEffect, useCallback, useRef } from "react";
import { fetchHealth } from "../api/health.ts";
import type { AiMode } from "../types/api.ts";

export type BackendStatus = "loading" | "online" | "offline";

export interface UseAiModeResult {
  status: BackendStatus;
  aiMode: AiMode;
  refresh: () => void;
}

export function useAiMode(): UseAiModeResult {
  const [status, setStatus] = useState<BackendStatus>("loading");
  const [aiMode, setAiMode] = useState<AiMode>("demo");
  const abortControllerRef = useRef<AbortController | null>(null);

  const checkHealth = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    fetchHealth(controller.signal)
      .then((data) => {
        setStatus("online");
        setAiMode(data.ai_mode || "demo");
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        // Graceful fallback when backend is offline
        setStatus("offline");
        setAiMode("demo");
      });
  }, []);

  useEffect(() => {
    checkHealth();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [checkHealth]);

  return {
    status,
    aiMode,
    refresh: checkHealth,
  };
}
