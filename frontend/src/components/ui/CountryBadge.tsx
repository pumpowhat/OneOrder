import type { NordicCountry } from "../../types/api";
import { cn } from "../../lib/cn";

export interface CountryBadgeProps {
  country: NordicCountry;
  className?: string;
}

export function CountryBadge({ country, className }: CountryBadgeProps) {
  return (
    <span
      className={cn(
        "font-mono text-[11px] font-semibold tracking-wider px-2 py-0.5 rounded border inline-flex items-center justify-center",
        "bg-surface-2 text-ink border-line-strong",
        className
      )}
    >
      {country}
    </span>
  );
}
