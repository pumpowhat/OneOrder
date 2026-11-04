import { apiClient } from "./client.ts";
import type { HealthResponse } from "../types/api.ts";

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/api/health", { signal });
}
