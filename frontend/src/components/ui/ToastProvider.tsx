import { useState, useCallback, type ReactNode } from "react";
import { X, CheckCircle2, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { ToastContext, type ToastItem, type ToastTone } from "./toastContext";
import { cn } from "../../lib/cn";

interface ToastProviderProps {
  children: ReactNode;
}

const TONE_ICONS: Record<ToastTone, typeof CheckCircle2> = {
  success: CheckCircle2,
  info: Info,
  warn: AlertTriangle,
  danger: AlertCircle,
};

const TONE_COLORS: Record<ToastTone, { border: string; icon: string }> = {
  success: { border: "border-success/30", icon: "text-success" },
  info: { border: "border-info/30", icon: "text-info" },
  warn: { border: "border-warn/30", icon: "text-warn" },
  danger: { border: "border-danger/30", icon: "text-danger" },
};

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    ({ title, description, tone = "info" }: Omit<ToastItem, "id">) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((prev) => [...prev, { id, title, description, tone }]);

      setTimeout(() => {
        dismissToast(id);
      }, 3500);
    },
    [dismissToast]
  );

  return (
    <ToastContext.Provider value={{ pushToast, dismissToast }}>
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((toast) => {
          const tone = toast.tone || "info";
          const Icon = TONE_ICONS[tone];
          const colors = TONE_COLORS[tone];

          return (
            <div
              key={toast.id}
              role="status"
              className={cn(
                "pointer-events-auto bg-surface border shadow-lg rounded-xl p-3.5 flex items-start gap-3 animate-page-enter",
                colors.border
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0 mt-0.5", colors.icon)} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-ink leading-tight">
                  {toast.title}
                </div>
                {toast.description && (
                  <div className="text-xs text-ink-muted mt-1 leading-snug">
                    {toast.description}
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => dismissToast(toast.id)}
                aria-label="Dismiss toast"
                className="text-ink-muted hover:text-ink transition-colors p-1 -mr-1 -mt-1 rounded-md cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
