import { BrowserRouter, Routes, Route } from "react-router";
import { ThemeProvider } from "./theme/ThemeProvider.tsx";
import { I18nProvider } from "./i18n/I18nProvider.tsx";
import { ToastProvider } from "./components/ui/ToastProvider.tsx";
import { AppShell } from "./components/layout/AppShell.tsx";

import DashboardPage from "./pages/DashboardPage.tsx";
import NewOrderPage from "./pages/NewOrderPage.tsx";
import OrdersPage from "./pages/OrdersPage.tsx";
import OrderDetailPage from "./pages/OrderDetailPage.tsx";
import StockPage from "./pages/StockPage.tsx";
import RulesPage from "./pages/RulesPage.tsx";
import NotFoundPage from "./pages/NotFoundPage.tsx";

export default function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<AppShell />}>
                <Route index element={<DashboardPage />} />
                <Route path="orders" element={<OrdersPage />} />
                <Route path="orders/new" element={<NewOrderPage />} />
                <Route path="orders/:id" element={<OrderDetailPage />} />
                <Route path="stock" element={<StockPage />} />
                <Route path="rules" element={<RulesPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
