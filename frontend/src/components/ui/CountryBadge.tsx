import type { NordicCountry } from "../../types/api";
import { cn } from "../../lib/cn";

export interface CountryBadgeProps {
  country: NordicCountry;
  className?: string;
}

const COUNTRY_STYLES: Record<NordicCountry, string> = {
  DK: "bg-danger-soft text-danger border-danger/30",
  SE: "bg-info-soft text-info border-info/30",
  NO: "bg-brand-soft text-brand-ink border-brand/30",
};

export function CountryBadge({ country, className }: CountryBadgeProps) {
  return (
    <span
      className={cn(
        "font-mono text-[11px] font-semibold tracking-wider px-2 py-0.5 rounded border inline-flex items-center justify-center",
        COUNTRY_STYLES[country] || "bg-surface-2 text-ink-muted border-line",
        className
      )}
    >
      {country}
    </span>
  );
}
