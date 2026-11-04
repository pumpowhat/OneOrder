import { createContext } from "react";

export type ToastTone = "success" | "info" | "warn" | "danger";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  tone?: ToastTone;
}

export interface ToastContextType {
  pushToast: (toast: Omit<ToastItem, "id">) => void;
  dismissToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextType | null>(null);
