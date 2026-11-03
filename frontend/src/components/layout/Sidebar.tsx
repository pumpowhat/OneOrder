import { NavLink } from "react-router";
import {
  Inbox,
  FileCheck2,
  Truck,
  Boxes,
  SlidersHorizontal,
  Activity,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useSidebar } from "./useSidebar.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";

export function Sidebar() {
  const { collapsed, toggleCollapsed } = useSidebar();
  const { t } = useI18n();

  const navItems = [
    { to: "/inbox", label: t("nav.inbox"), icon: Inbox },
    { to: "/review", label: t("nav.review"), icon: FileCheck2 },
    { to: "/plan", label: t("nav.plan"), icon: Truck },
    { to: "/stock", label: t("nav.stock"), icon: Boxes },
    { to: "/rules", label: t("nav.rules"), icon: SlidersHorizontal },
    { to: "/model", label: t("nav.model"), icon: Activity },
  ];

  return (
    <aside
      className={cn(
        "bg-sidebar text-sidebar-ink border-r border-sidebar-line flex flex-col justify-between shrink-0 select-none z-30 transition-[width] duration-200 ease-out",
        collapsed ? "w-[72px]" : "w-[248px]",
      )}
    >
      <div>
        {/* Brand bar */}
        <div className="h-14 border-b border-sidebar-line flex items-center px-4 gap-3">
          <svg
            className="w-8 h-8 shrink-0"
            viewBox="0 0 32 32"
            fill="none"
            aria-hidden="true"
          >
            <rect width="32" height="32" rx="8" fill="var(--brand)" />
            <path
              d="M16 6L25 11.2V20.8L16 26L7 20.8V11.2L16 6Z"
              stroke="var(--on-brand)"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path
              d="M7 11.2L16 16.4L25 11.2M16 16.4V26"
              stroke="var(--sidebar-accent)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {!collapsed && (
            <div className="overflow-hidden whitespace-nowrap leading-tight">
              <div className="font-semibold text-sidebar-ink-strong text-base tracking-tight">
                OneOrder
              </div>
              <div className="text-[11px] text-sidebar-ink">
                {t("header.nordicOps")}
              </div>
            </div>
          )}
        </div>

        {/* Main Nav */}
        <nav aria-label="Main navigation" className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                    isActive
                      ? "bg-sidebar-active text-sidebar-ink-strong border-l-2 border-sidebar-accent"
                      : "text-sidebar-ink hover:text-sidebar-ink-strong hover:bg-sidebar-hover",
                    collapsed && "justify-center px-0",
                  )
                }
              >
                <Icon className="w-5 h-5 shrink-0 text-sidebar-accent" />
                {!collapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Collapse footer button */}
      <div className="p-3 border-t border-sidebar-line">
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label={collapsed ? t("header.expandNav") : t("header.collapseNav")}
          className={cn(
            "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-sidebar-ink hover:text-sidebar-ink-strong hover:bg-sidebar-hover transition-colors cursor-pointer",
            collapsed && "justify-center px-0",
          )}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4 shrink-0" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4 shrink-0" />
              <span>{t("header.collapseNav")}</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
