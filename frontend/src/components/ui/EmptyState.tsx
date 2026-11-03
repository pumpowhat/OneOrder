import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "bg-surface border border-line rounded-card p-10 text-center flex flex-col items-center justify-center space-y-3",
        className
      )}
    >
      {icon && (
        <div className="w-10 h-10 rounded-full bg-surface-2 flex items-center justify-center text-ink-muted">
          {icon}
        </div>
      )}
      <div className="space-y-1 max-w-sm">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <p className="text-xs text-ink-muted">{description}</p>
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
