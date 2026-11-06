import { NavLink } from "react-router";
import { Logo } from "../shared/Logo.tsx";
import { AiModeBadge } from "../shared/AiModeBadge.tsx";
import { LanguageSwitcher } from "../shared/LanguageSwitcher.tsx";
import { ThemeToggle } from "../../theme/ThemeToggle.tsx";
import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";

export function TopNav() {
  const { t } = useI18n();
  const items = [
    { to: "/", label: t("nav.dashboard"), end: true },
    { to: "/orders", label: t("nav.orders"), end: false },
    { to: "/stock", label: t("nav.stock"), end: false },
  ];

  return (
    <header className="sticky top-0 z-20 bg-surface border-b border-line">
      <div className="mx-auto max-w-[1200px] px-6 h-14 flex items-center gap-8">
        <NavLink to="/" className="shrink-0" aria-label="OneOrder">
          <Logo />
        </NavLink>

        <nav aria-label="Main" className="flex items-center gap-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  isActive ? "bg-brand-soft text-brand-ink" : "text-ink-muted hover:text-ink hover:bg-surface-2",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <AiModeBadge />
          <ThemeToggle />
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
