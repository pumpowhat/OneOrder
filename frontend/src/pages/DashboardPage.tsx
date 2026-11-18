import { Link } from "react-router";
import { AlertTriangle, ChevronRight } from "lucide-react";
import { listOrders } from "../api/orders.ts";
import { useApi } from "../hooks/useApi.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";
import type { TranslationKey } from "../i18n/en.ts";
import { errorMessage } from "../lib/errors.ts";
import { formatIsoDate } from "../lib/format.ts";
import type { OrderStatus, OrderSummary } from "../types/api.ts";
import { Card, CardBody, CardHeader } from "../components/ui/Card.tsx";
import { EmptyState } from "../components/ui/EmptyState.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";
import { RiskBadge } from "../components/orders/StatusBadge.tsx";
import { UploadButton } from "../components/orders/UploadZone.tsx";

interface Attention {
  order: OrderSummary;
  tone: "danger" | "warn";
  text: string;
}

const STATS: Array<{ status: OrderStatus; label: TranslationKey; hint: TranslationKey }> = [
  { status: "draft", label: "dash.toReview", hint: "dash.toReviewHint" },
  { status: "approved", label: "dash.toPlan", hint: "dash.toPlanHint" },
  { status: "planned", label: "dash.toConfirm", hint: "dash.toConfirmHint" },
  { status: "confirmed", label: "dash.confirmed", hint: "dash.confirmedHint" },
];

export default function DashboardPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.dashboard"));
  const { data, error, loading, reload } = useApi((signal) => listOrders(undefined, signal), []);
  const orders = data ?? [];

  const pendingSync = orders.filter((order) => order.crm_sync_status === "pending" || order.crm_sync_status === "failed").length;
  const syncCountAvailable = orders.every((order) => order.status !== "confirmed" || order.crm_sync_status !== undefined);
  const count = (status: OrderStatus) => orders.filter((o) => o.status === status).length;

  const attention: Attention[] = [];
  for (const order of orders) {
    const who = order.customer ?? order.source_name ?? "—";
    if (order.status === "draft" && order.review_lines > 0) {
      attention.push({ order, tone: "warn", text: t("dash.reviewLines", { who, n: order.review_lines }) });
    }
    if (order.status === "planned" || order.status === "confirmed") {
      if (order.risk === "late") {
        attention.push({ order, tone: "danger", text: t("dash.late", { who, date: formatIsoDate(order.requested_date) }) });
      } else if (order.risk === "at_risk") {
        attention.push({ order, tone: "warn", text: t("dash.atRisk", { who, date: formatIsoDate(order.requested_date) }) });
      }
      if (order.shortage_count > 0) {
        attention.push({ order, tone: "danger", text: t("dash.shortage", { who, n: order.shortage_count }) });
      }
    }
  }
  attention.sort((a, b) => (a.tone === b.tone ? 0 : a.tone === "danger" ? -1 : 1));

  const deliveries = orders
    .filter((o) => (o.status === "planned" || o.status === "confirmed") && o.p50_date)
    .sort((a, b) => (a.p50_date ?? "").localeCompare(b.p50_date ?? ""))
    .slice(0, 6);

  return (
    <div className="space-y-6">
      <PageHeader title={t("nav.dashboard")} subtitle={t("dash.subtitle")} actions={<UploadButton />} />

      {error && (
        <Card>
          <CardBody className="flex items-center justify-between gap-4">
            <span className="text-sm text-danger">{errorMessage(error, t)}</span>
            <button type="button" onClick={reload} className="text-sm font-medium text-info hover:underline">
              {t("common.retry")}
            </button>
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {STATS.map((stat) => (
          <Link
            key={stat.status}
            to={`/orders?tab=${stat.status}`}
            className="bg-surface border border-line rounded-card shadow-card p-5 hover:border-accent transition-colors"
          >
            <div className="font-display text-3xl font-semibold tabular-nums">{loading ? "…" : count(stat.status)}</div>
            <div className="mt-1 text-sm font-medium">{t(stat.label)}</div>
            <div className="text-xs text-ink-muted">{t(stat.hint)}</div>
          </Link>
        ))}
        <Card>
          <CardBody className="p-5">
            <div className="font-display text-3xl font-semibold tabular-nums">
              {loading ? "…" : !syncCountAvailable ? "—" : pendingSync}
            </div>
            <div className="mt-1 text-sm font-medium">{t("crm.pendingOrders")}</div>
            <div className="text-xs text-ink-muted">{t("crm.pendingOrdersHint")}</div>
          </CardBody>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">{t("dash.attention")}</h2>
          </CardHeader>
          {attention.length === 0 ? (
            <CardBody className="text-sm text-ink-muted">{loading ? t("common.loading") : t("dash.attentionEmpty")}</CardBody>
          ) : (
            <ul className="divide-y divide-line">
              {attention.slice(0, 6).map((item, i) => (
                <li key={`${item.order.id}-${i}`}>
                  <Link to={`/orders/${item.order.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-surface-2">
                    <AlertTriangle className={item.tone === "danger" ? "w-4 h-4 text-danger shrink-0" : "w-4 h-4 text-warn shrink-0"} />
                    <span className="text-sm flex-1">{item.text}</span>
                    <ChevronRight className="w-4 h-4 text-ink-faint" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">{t("dash.deliveries")}</h2>
          </CardHeader>
          {deliveries.length === 0 ? (
            <CardBody className="text-sm text-ink-muted">{loading ? t("common.loading") : t("dash.deliveriesEmpty")}</CardBody>
          ) : (
            <ul className="divide-y divide-line">
              {deliveries.map((order) => (
                <li key={order.id}>
                  <Link to={`/orders/${order.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-surface-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{order.customer ?? order.source_name ?? "—"}</div>
                      <div className="text-xs text-ink-muted tabular-nums">
                        {formatIsoDate(order.p50_date)} – {formatIsoDate(order.p90_date)}
                      </div>
                    </div>
                    <RiskBadge risk={order.risk} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {!loading && !error && orders.length === 0 && (
        <EmptyState title={t("dash.emptyTitle")} description={t("dash.emptyText")} action={<UploadButton variant="primary" />} />
      )}
    </div>
  );
}
