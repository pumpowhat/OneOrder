import { Sidebar } from "./Sidebar.tsx";
import { Header } from "./Header.tsx";
import { PageTransition } from "./PageTransition.tsx";

export function AppShell() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-canvas text-ink">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Header />
        <main
          id="main-content"
          className="flex-1 overflow-y-auto scrollbar-stable p-6"
        >
          <div className="mx-auto max-w-[1360px]">
            <PageTransition />
          </div>
        </main>
      </div>
    </div>
  );
}
