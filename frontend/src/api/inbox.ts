import { apiClient } from "./client.ts";
import type { InboxItem } from "../types/api.ts";

export function listInbox(signal?: AbortSignal) {
  return apiClient<InboxItem[]>("/api/inbox", { signal });
}

export function importInboxItem(id: string) {
  return apiClient<{ id: string }>("/api/inbox/import", { method: "POST", body: { id } });
}
