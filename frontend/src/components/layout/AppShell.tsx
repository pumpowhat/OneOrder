import { TopNav } from "./TopNav.tsx";
import { PageTransition } from "./PageTransition.tsx";

export function AppShell() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <TopNav />
      <main id="main-content" className="mx-auto max-w-[1200px] px-6 py-8">
        <PageTransition />
      </main>
    </div>
  );
}
