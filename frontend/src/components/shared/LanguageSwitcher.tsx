import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div
      role="group"
      aria-label="Language selection"
      className="inline-flex items-center rounded-lg border border-line bg-surface-2 p-0.5 text-xs font-semibold"
    >
      <button
        type="button"
        onClick={() => setLocale("en")}
        aria-pressed={locale === "en"}
        className={cn(
          "cursor-pointer px-2 py-1 rounded-md transition-colors",
          locale === "en"
            ? "bg-surface text-ink shadow-sm"
            : "text-ink-muted hover:text-ink",
        )}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLocale("vi")}
        aria-pressed={locale === "vi"}
        className={cn(
          "cursor-pointer px-2 py-1 rounded-md transition-colors",
          locale === "vi"
            ? "bg-surface text-ink shadow-sm"
            : "text-ink-muted hover:text-ink",
        )}
      >
        VI
      </button>
    </div>
  );
}
