import { apiClient } from "./client.ts";
import type { ModelInfo, NordicCountry, StockResponse } from "../types/api.ts";

export interface StockQuery {
  country?: NordicCountry;
  q?: string;
  onlyIssues?: boolean;
}

export function getStock({ country, q, onlyIssues }: StockQuery, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (country) params.set("country", country);
  if (q?.trim()) params.set("q", q.trim());
  if (onlyIssues) params.set("only_issues", "true");
  const query = params.toString();
  return apiClient<StockResponse>(`/api/stock${query ? `?${query}` : ""}`, { signal });
}

export function getModelInfo(signal?: AbortSignal) {
  return apiClient<ModelInfo>("/api/model", { signal });
}
