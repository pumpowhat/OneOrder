import { cn } from "../../lib/cn";
import { formatPercent } from "../../lib/format";

export interface ConfidenceBarProps {
  value: number; // 0 to 1
  threshold?: number; // default 0.85
  showLabel?: boolean;
  className?: string;
}

export function ConfidenceBar({
  value,
  threshold = 0.85,
  showLabel = true,
  className,
}: ConfidenceBarProps) {
  const clamped = Math.max(0, Math.min(1, value));
  const isHigh = clamped >= threshold;
  const isMedium = clamped >= 0.7;

  const barColor = isHigh
    ? "bg-success"
    : isMedium
      ? "bg-warn"
      : "bg-danger";

  const textColor = isHigh
    ? "text-success"
    : isMedium
      ? "text-warn"
      : "text-danger";

  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <div
        className="w-16 h-1.5 bg-surface-2 rounded-full overflow-hidden border border-line"
        role="progressbar"
        aria-valuenow={Math.round(clamped * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn("h-full rounded-full transition-all duration-300", barColor)}
          style={{ width: `${clamped * 100}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn("font-mono text-xs font-semibold", textColor)}>
          {formatPercent(clamped)}
        </span>
      )}
    </div>
  );
}
