import type { ReactNode } from "react";
import { cn } from "../../lib/cn.ts";

export type BadgeTone =
  | "neutral"
  | "brand"
  | "success"
  | "warn"
  | "danger"
  | "info";

export interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}

const TONE_STYLES: Record<BadgeTone, string> = {
  neutral: "bg-surface-2 text-ink-muted border-line-strong",
  brand: "bg-brand-soft text-brand-ink border-line-strong",
  success: "bg-success-soft text-success border-success/20",
  warn: "bg-warn-soft text-warn border-warn/20",
  danger: "bg-danger-soft text-danger border-danger/20",
  info: "bg-info-soft text-info border-info/20",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-0.5 text-xs font-medium inline-flex items-center gap-1.5 border",
        TONE_STYLES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
