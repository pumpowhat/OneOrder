import { useI18n } from "../../i18n/useI18n.ts";
import { TopNav } from "./TopNav.tsx";
import { PageTransition } from "./PageTransition.tsx";

export function AppShell() {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <TopNav />
      <main id="main-content" className="mx-auto max-w-[1200px] px-6 py-8">
        <PageTransition />
      </main>
      <footer className="pb-8 text-center text-xs text-ink-faint">{t("brand.tagline")}</footer>
    </div>
  );
}
