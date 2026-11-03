import { cn } from "../../lib/cn";

export interface SegmentedOption<T extends string> {
  value: T;
  label: string;
  count?: number;
}

export interface SegmentedProps<T extends string> {
  options: Array<SegmentedOption<T>>;
  value: T;
  onChange: (value: T) => void;
  className?: string;
  size?: "sm" | "md";
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  className,
  size = "md",
}: SegmentedProps<T>) {
  return (
    <div
      role="radiogroup"
      className={cn(
        "bg-surface-2 p-1 rounded-lg inline-flex items-center gap-1 border border-line",
        className
      )}
    >
      {options.map((opt) => {
        const isSelected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(opt.value)}
            className={cn(
              "rounded-md font-medium transition-all cursor-pointer flex items-center gap-1.5",
              size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-xs",
              isSelected
                ? "bg-surface text-ink shadow-sm"
                : "text-ink-muted hover:text-ink hover:bg-surface/50"
            )}
          >
            <span>{opt.label}</span>
            {typeof opt.count === "number" && (
              <span
                className={cn(
                  "px-1.5 py-0.2 rounded-full text-[10px] font-semibold",
                  isSelected
                    ? "bg-surface-2 text-ink"
                    : "bg-line text-ink-muted"
                )}
              >
                {opt.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
