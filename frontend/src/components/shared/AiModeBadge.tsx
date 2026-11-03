import { useAiMode } from "../../hooks/useAiMode.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";

export function AiModeBadge() {
  const { status, aiMode, refresh } = useAiMode();
  const { t } = useI18n();

  const isLive = status === "online" && aiMode === "live";
  const isDemoOnline = status === "online" && aiMode === "demo";
  const isOffline = status === "offline";

  return (
    <button
      type="button"
      onClick={refresh}
      title="Click to recheck /api/health"
      aria-label="API status and AI mode"
      className={cn(
        "cursor-pointer rounded-full px-2.5 py-1 text-xs font-medium inline-flex items-center gap-1.5 transition-colors border",
        isLive && "bg-success-soft text-success border-success/30 hover:bg-success-soft/80",
        isDemoOnline && "bg-info-soft text-info border-info/30 hover:bg-info-soft/80",
        isOffline && "bg-warn-soft text-warn border-warn/30 hover:bg-warn-soft/80",
        status === "loading" && "bg-surface-2 text-ink-muted border-line",
      )}
    >
      <span className="relative flex h-2 w-2">
        {isLive && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
        )}
        <span
          className={cn(
            "relative inline-flex rounded-full h-2 w-2",
            isLive && "bg-success",
            isDemoOnline && "bg-info",
            isOffline && "bg-warn",
            status === "loading" && "bg-ink-faint",
          )}
        />
      </span>
      <span>
        {isLive
          ? t("header.aiLive")
          : isDemoOnline
            ? t("header.aiDemo")
            : isOffline
              ? t("header.aiOffline")
              : t("common.loading")}
      </span>
    </button>
  );
}
