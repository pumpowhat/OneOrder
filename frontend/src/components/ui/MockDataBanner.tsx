import { Sparkles } from "lucide-react";
import { cn } from "../../lib/cn";
import { useI18n } from "../../i18n/useI18n";

export interface MockDataBannerProps {
  note?: string;
  className?: string;
}

export function MockDataBanner({ note, className }: MockDataBannerProps) {
  const { t } = useI18n();

  return (
    <div
      className={cn(
        "bg-brand-soft/60 border border-line rounded-lg px-3.5 py-2 text-xs text-ink-muted flex items-center justify-between mb-6",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-3.5 h-3.5 text-brand shrink-0" />
        <span>{note || t("mockBanner.text")}</span>
      </div>
      <span className="font-mono text-[11px] uppercase tracking-wider text-brand-ink bg-brand-soft px-2 py-0.5 rounded border border-brand/20 shrink-0">
        Sample Mode
      </span>
    </div>
  );
}
