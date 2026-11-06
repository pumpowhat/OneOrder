import { apiClient } from "./client.ts";
import type { Rules } from "../types/api.ts";

export function getRules(signal?: AbortSignal) {
  return apiClient<Rules>("/api/rules", { signal });
}

export function saveRules(rules: Rules) {
  return apiClient<Rules>("/api/rules", { method: "PUT", body: rules });
}
