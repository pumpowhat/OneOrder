import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { ThemeProvider } from "./theme/ThemeProvider.tsx";
import { I18nProvider } from "./i18n/I18nProvider.tsx";
import { SidebarProvider } from "./components/layout/SidebarProvider.tsx";
import { ToastProvider } from "./components/ui/ToastProvider.tsx";
import { AppShell } from "./components/layout/AppShell.tsx";

import InboxPage from "./pages/InboxPage.tsx";
import ReviewPage from "./pages/ReviewPage.tsx";
import PlanPage from "./pages/PlanPage.tsx";
import StockPage from "./pages/StockPage.tsx";
import RulesPage from "./pages/RulesPage.tsx";
import ModelPage from "./pages/ModelPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";

export default function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <ToastProvider>
          <SidebarProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<AppShell />}>
                  <Route index element={<Navigate to="/inbox" replace />} />
                  <Route path="inbox" element={<InboxPage />} />
                  <Route path="review" element={<ReviewPage />} />
                  <Route path="plan" element={<PlanPage />} />
                  <Route path="stock" element={<StockPage />} />
                  <Route path="rules" element={<RulesPage />} />
                  <Route path="model" element={<ModelPage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </SidebarProvider>
        </ToastProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
