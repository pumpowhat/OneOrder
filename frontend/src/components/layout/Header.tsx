import { User, Globe } from "lucide-react";
import { AiModeBadge } from "../shared/AiModeBadge.tsx";
import { LanguageSwitcher } from "../shared/LanguageSwitcher.tsx";
import { ThemeToggle } from "../../theme/ThemeToggle.tsx";
import { useI18n } from "../../i18n/useI18n.ts";

export function Header() {
  const { t } = useI18n();

  return (
    <header className="sticky top-0 h-14 bg-surface border-b border-line px-6 flex items-center justify-between z-20 select-none">
      {/* Left market indicator / breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 border border-line text-xs font-semibold text-ink-muted">
          <Globe className="w-3.5 h-3.5 text-brand" />
          <span>{t("header.marketBadge")}</span>
        </div>
        <span className="text-xs text-ink-faint">/</span>
        <span className="text-xs font-medium text-ink-muted">
          {t("header.nordicOps")}
        </span>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        <AiModeBadge />
        <div className="h-4 w-px bg-line" aria-hidden="true" />
        <ThemeToggle />
        <LanguageSwitcher />
        <div className="h-4 w-px bg-line" aria-hidden="true" />
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-2 border border-line text-xs font-medium text-ink">
          <User className="w-3.5 h-3.5 text-ink-muted" />
          <span>{t("header.operator")}</span>
        </div>
      </div>
    </header>
  );
}
