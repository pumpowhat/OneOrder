import { apiClient } from "./client.ts";
import type {
  LineAvailability,
  LineCorrection,
  FulfillmentPlan,
  Order,
  OrderSource,
  OrderStatus,
  OrderSummary,
  Site,
} from "../types/api.ts";

export function listOrders(status?: OrderStatus, signal?: AbortSignal) {
  const query = status ? `?status=${status}` : "";
  return apiClient<OrderSummary[]>(`/api/orders${query}`, { signal });
}

export function getOrder(id: string, signal?: AbortSignal) {
  return apiClient<Order>(`/api/orders/${id}`, { signal });
}

export function uploadOrder(file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiClient<{ id: string }>("/api/intake", { method: "POST", body: form });
}

export function uploadOrderText(text: string) {
  const form = new FormData();
  form.append("text", text);
  return apiClient<{ id: string }>("/api/intake", { method: "POST", body: form });
}

export function getOrderSource(id: string, signal?: AbortSignal) {
  return apiClient<OrderSource>(`/api/orders/${id}/source`, { signal });
}

export const orderSourceFileUrl = (id: string) => `/api/orders/${id}/source/file`;

export function getAvailability(id: string, signal?: AbortSignal) {
  return apiClient<LineAvailability[]>(`/api/orders/${id}/availability`, { signal });
}

export function approveOrder(id: string, corrections: LineCorrection[], confirmLines: number[], customer?: string) {
  return apiClient<Order>(`/api/orders/${id}/approve`, {
    method: "POST",
    body: { corrections, confirm_lines: confirmLines, ...(customer ? { customer } : {}) },
  });
}

export function planOrder(id: string, siteId?: string) {
  return apiClient<FulfillmentPlan>(`/api/orders/${id}/plan`, {
    method: "POST",
    body: siteId ? { site_id: siteId } : {},
  });
}

export function confirmOrder(id: string, flags: { allow_partial: boolean; accept_late_risk: boolean }) {
  return apiClient<Order>(`/api/orders/${id}/confirm`, { method: "POST", body: flags });
}

export function cancelOrder(id: string) {
  return apiClient<Order>(`/api/orders/${id}/cancel`, { method: "POST", body: {} });
}

export function listSites(signal?: AbortSignal) {
  return apiClient<Site[]>("/api/sites", { signal });
}
