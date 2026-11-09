import { Link, useNavigate, useSearchParams } from "react-router";
import { FileImage, FileSpreadsheet, FileText, Mail } from "lucide-react";
import { listOrders } from "../api/orders.ts";
import { useApi } from "../hooks/useApi.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";
import type { TranslationKey } from "../i18n/en.ts";
import { errorMessage } from "../lib/errors.ts";
import { formatIsoDate } from "../lib/format.ts";
import type { OrderStatus, OrderSummary, SourceType } from "../types/api.ts";
import { Button } from "../components/ui/Button.tsx";
import { Badge } from "../components/ui/Badge.tsx";
import { Card, CardBody } from "../components/ui/Card.tsx";
import { EmptyState } from "../components/ui/EmptyState.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";
import { Segmented } from "../components/ui/Segmented.tsx";
import { RiskBadge, StatusBadge } from "../components/orders/StatusBadge.tsx";
import { InboxPanel } from "../components/orders/InboxPanel.tsx";
import { UploadZone } from "../components/orders/UploadZone.tsx";

type Tab = OrderStatus | "all";
const TABS: Array<{ value: Tab; label: TranslationKey }> = [
  { value: "draft", label: "orders.tabReview" },
  { value: "approved", label: "orders.tabPlan" },
  { value: "planned", label: "orders.tabConfirm" },
  { value: "confirmed", label: "orders.tabConfirmed" },
  { value: "all", label: "orders.tabAll" },
];

const SOURCE_ICON: Record<SourceType, typeof Mail> = { image: FileImage, pdf: FileText, excel: FileSpreadsheet, email: Mail, manual: FileText };

function note(order: OrderSummary, t: ReturnType<typeof useI18n>["t"]) {
  if (order.status === "draft" && order.review_lines > 0) {
    return <Badge tone="warn">{t("orders.linesToReview", { n: order.review_lines })}</Badge>;
  }
  if ((order.status === "planned" || order.status === "confirmed") && order.p50_date) {
    return (
      <span className="inline-flex items-center gap-2">
        <span className="text-xs text-ink-muted tabular-nums">{formatIsoDate(order.p50_date)}</span>
        <RiskBadge risk={order.risk} />
      </span>
    );
  }
  return null;
}

export default function OrdersPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.orders"));
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const tab = (params.get("tab") as Tab | null) ?? "draft";
  const { data, error, loading, reload } = useApi((signal) => listOrders(undefined, signal), []);
  const orders = data ?? [];

  const inTab = (o: OrderSummary, value: Tab) => (value === "all" ? true : o.status === value);
  const rows = orders.filter((o) => inTab(o, tab));

  return (
    <div className="space-y-6">
      <PageHeader title={t("nav.orders")} subtitle={t("orders.subtitle")} actions={<Link to="/orders/new"><Button variant="accent">{t("draft.create")}</Button></Link>} />
      <UploadZone />
      <InboxPanel defaultOpen={!loading && orders.length === 0} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Segmented
          options={TABS.map((x) => ({ value: x.value, label: t(x.label), count: orders.filter((o) => inTab(o, x.value)).length }))}
          value={tab}
          onChange={(value) => setParams(value === "draft" ? {} : { tab: value })}
        />
      </div>

      {error ? (
        <Card>
          <CardBody className="flex items-center justify-between gap-4">
            <span className="text-sm text-danger">{errorMessage(error, t)}</span>
            <button type="button" onClick={reload} className="text-sm font-medium text-info hover:underline">
              {t("common.retry")}
            </button>
          </CardBody>
        </Card>
      ) : loading ? (
        <p className="text-sm text-ink-muted">{t("common.loading")}</p>
      ) : rows.length === 0 ? (
        <EmptyState title={t("orders.emptyTitle")} description={t("orders.emptyText")} />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-muted border-b border-line bg-surface-2">
                <th className="px-5 py-2.5 font-medium">{t("common.customer")}</th>
                <th className="px-3 py-2.5 font-medium hidden md:table-cell">{t("common.site")}</th>
                <th className="px-3 py-2.5 font-medium hidden lg:table-cell">{t("common.requestedDate")}</th>
                <th className="px-3 py-2.5 font-medium">{t("common.status")}</th>
                <th className="px-5 py-2.5 font-medium text-right" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((order) => {
                const Icon = SOURCE_ICON[order.source_type];
                return (
                  <tr
                    key={order.id}
                    onClick={() => navigate(`/orders/${order.id}`)}
                    className="hover:bg-surface-2 cursor-pointer"
                  >
                    <td className="px-5 py-3">
                      <Link to={`/orders/${order.id}`} className="flex items-center gap-3 font-medium" onClick={(e) => e.stopPropagation()}>
                        <Icon className="w-4 h-4 text-ink-faint shrink-0" aria-hidden="true" />
                        <span className="min-w-0">
                          <span className="block truncate">{order.customer ?? t("common.unknownCustomer")}</span>
                          {order.customer_phone && (
                            <span className="block text-xs font-normal text-ink-muted tabular-nums" aria-label={t("common.customerPhone")}>
                              {order.customer_phone}
                            </span>
                          )}
                          <span className="block text-xs font-normal text-ink-muted truncate">
                            {order.source_type === "manual" ? t("draft.manual") : order.source_name} · {t("orders.lines", { n: order.line_count })}
                          </span>
                        </span>
                      </Link>
                    </td>
                    <td className="px-3 py-3 text-ink-muted hidden md:table-cell max-w-[260px] truncate">{order.delivery_site ?? "—"}</td>
                    <td className="px-3 py-3 text-ink-muted tabular-nums hidden lg:table-cell">{formatIsoDate(order.requested_date)}</td>
                    <td className="px-3 py-3">
                      <StatusBadge status={order.status} />
                    </td>
                    <td className="px-5 py-3 text-right">{note(order, t)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
