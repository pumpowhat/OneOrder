import { useState } from "react";
import { Link, useParams } from "react-router";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { approveOrder, cancelOrder, confirmOrder, getAvailability, getOrder, listSites, planOrder } from "../api/orders.ts";
import { useApi } from "../hooks/useApi.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";
import { errorMessage } from "../lib/errors.ts";
import { formatIsoDate } from "../lib/format.ts";
import type { LineCorrection } from "../types/api.ts";
import { Button } from "../components/ui/Button.tsx";
import { Card, CardBody, CardHeader } from "../components/ui/Card.tsx";
import { EmptyState } from "../components/ui/EmptyState.tsx";
import { useToast } from "../components/ui/useToast.ts";
import { AuditTrail } from "../components/orders/AuditTrail.tsx";
import { PlanView } from "../components/orders/PlanView.tsx";
import { ReservationList } from "../components/orders/ReservationList.tsx";
import { ReviewLines } from "../components/orders/ReviewLines.tsx";
import { SourceViewer } from "../components/orders/SourceViewer.tsx";
import { Stepper } from "../components/orders/Stepper.tsx";
import { StatusBadge } from "../components/orders/StatusBadge.tsx";

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-ink-muted">{label}</div>
      <div className="text-sm font-medium truncate">{value}</div>
    </div>
  );
}

export default function OrderDetailPage() {
  const { id = "" } = useParams();
  const { t } = useI18n();
  const { pushToast } = useToast();
  const { data: loaded, error, loading, reload } = useApi((signal) => getOrder(id, signal), [id]);
  const order = loaded && loaded.id === id ? loaded : null;
  const status = order?.status;
  const availability = useApi(
    (signal) => (status === "draft" ? getAvailability(id, signal) : Promise.resolve([])),
    [id, status],
  );
  const sites = useApi((signal) => (status === "approved" ? listSites(signal) : Promise.resolve([])), [status]);

  const [busy, setBusy] = useState(false);
  const [siteId, setSiteId] = useState("");
  const [acceptShortage, setAcceptShortage] = useState(false);
  const [acceptLate, setAcceptLate] = useState(false);
  useDocumentTitle(order?.customer ?? t("nav.orders"));

  /** Run one backend action, show a toast either way and refresh the order. */
  const run = async (action: () => Promise<unknown>, okTitle: string) => {
    setBusy(true);
    try {
      await action();
      pushToast({ tone: "success", title: okTitle });
      reload();
    } catch (err) {
      pushToast({ tone: "danger", title: t("error.actionFailed"), description: errorMessage(err, t) });
    } finally {
      setBusy(false);
    }
  };

  if (loading && !order) return <p className="text-sm text-ink-muted">{t("common.loading")}</p>;
  if (error || !order) {
    return (
      <EmptyState
        title={t("order.notFound")}
        description={error ? errorMessage(error, t) : ""}
        action={
          <Link to="/orders">
            <Button variant="primary">{t("order.back")}</Button>
          </Link>
        }
      />
    );
  }

  const plan = order.plan;
  const needsShortageOk = !!plan && plan.shortages.length > 0;
  const needsLateOk = plan?.order_eta?.risk === "late";
  const canConfirm = (!needsShortageOk || acceptShortage) && (!needsLateOk || acceptLate);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <Link to="/orders" className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink">
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          {t("order.back")}
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-2xl font-semibold tracking-tight">{order.customer ?? t("common.unknownCustomer")}</h1>
              <StatusBadge status={order.status} />
            </div>
            <p className="text-sm text-ink-muted">{order.source_name}</p>
          </div>
          {order.status !== "cancelled" && <Stepper status={order.status} />}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 bg-surface border border-line rounded-card p-4">
          <Meta label={t("common.customer")} value={order.customer ?? "—"} />
          <Meta label={t("common.customerPhone")} value={order.customer_phone ?? "—"} />
          <Meta label={t("common.site")} value={order.delivery_site ?? "—"} />
          <Meta label={t("common.requestedDate")} value={formatIsoDate(order.requested_date)} />
        </div>
      </div>

      {order.status === "cancelled" && (
        <div role="status" className="rounded-card border border-line bg-surface-2 px-5 py-4 text-sm text-ink-muted">
          {t("order.cancelled")}
        </div>
      )}

      {order.warnings.length > 0 && order.status === "draft" && (
        <ul className="rounded-card border border-warn/30 bg-warn-soft px-5 py-3 text-sm text-warn space-y-0.5">
          {order.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {/* Step 1: compare the original with what the system read, then approve */}
      {order.status === "draft" && (
        <div className="grid lg:grid-cols-2 gap-6 items-start">
          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold">{t("review.original")}</h2>
            </CardHeader>
            {order.has_source ? <SourceViewer orderId={order.id} /> : <CardBody className="text-sm text-ink-muted">{t("source.missing")}</CardBody>}
          </Card>
          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold">{t("review.result")}</h2>
              <span className="text-xs text-ink-muted">{t("orders.lines", { n: order.lines.length })}</span>
            </CardHeader>
            <ReviewLines
              key={order.id}
              order={order}
              availability={availability.data ?? []}
              busy={busy}
              onApprove={(corrections: LineCorrection[], confirmLines: number[], customer?: string, customerPhone?: string) =>
                run(() => approveOrder(order.id, corrections, confirmLines, customer, customerPhone), t("review.approved"))
              }
            />
          </Card>
        </div>
      )}

      {/* Step 2: plan */}
      {order.status === "approved" && (
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">{t("plan.make")}</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <p className="text-sm text-ink-muted">{t("plan.makeHint")}</p>
            <label className="block max-w-md space-y-1.5">
              <span className="text-xs text-ink-muted">{t("common.site")}</span>
              <select
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                className="w-full h-9 px-2 rounded-md border border-line-strong bg-surface text-sm"
              >
                <option value="">{t("plan.autoSite", { site: order.delivery_site ?? "—" })}</option>
                {(sites.data ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.country} · {s.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="accent" disabled={busy} onClick={() => run(() => planOrder(order.id, siteId || undefined), t("plan.made"))}>
                {busy ? t("common.working") : t("plan.make")}
              </Button>
              <Button variant="ghost" disabled={busy} onClick={() => run(() => cancelOrder(order.id), t("order.cancelDone"))}>
                {t("order.cancel")}
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Step 3: look at the plan and ETA, then confirm */}
      {(order.status === "planned" || order.status === "confirmed") && plan && <PlanView plan={plan} />}

      {order.status === "planned" && plan && (
        <Card>
          <CardBody className="space-y-4">
            {needsShortageOk && (
              <label className="flex items-start gap-2.5 text-sm cursor-pointer">
                <input type="checkbox" checked={acceptShortage} onChange={(e) => setAcceptShortage(e.target.checked)} className="mt-0.5 w-4 h-4 accent-[var(--brand)]" />
                {t("confirm.acceptShortage")}
              </label>
            )}
            {needsLateOk && (
              <label className="flex items-start gap-2.5 text-sm cursor-pointer">
                <input type="checkbox" checked={acceptLate} onChange={(e) => setAcceptLate(e.target.checked)} className="mt-0.5 w-4 h-4 accent-[var(--brand)]" />
                {t("confirm.acceptLate")}
              </label>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="accent"
                disabled={busy || !canConfirm}
                onClick={() =>
                  run(
                    () => confirmOrder(order.id, { allow_partial: acceptShortage, accept_late_risk: acceptLate }),
                    t("confirm.done"),
                  )
                }
              >
                {busy ? t("common.working") : t("confirm.button")}
              </Button>
              <Button disabled={busy} onClick={() => run(() => planOrder(order.id), t("plan.made"))}>
                {t("plan.redo")}
              </Button>
              <Button variant="ghost" disabled={busy} onClick={() => run(() => cancelOrder(order.id), t("order.cancelDone"))}>
                {t("order.cancel")}
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {order.status === "confirmed" && (
        <div role="status" className="rounded-card border border-success/30 bg-success-soft px-5 py-4 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-success shrink-0 mt-0.5" aria-hidden="true" />
          <div className="space-y-0.5">
            <div className="text-sm font-semibold text-success">{t("confirm.confirmed")}</div>
            <div className="text-sm text-success">{t("confirm.reserved", { n: order.reservations.length })}</div>
          </div>
        </div>
      )}

      {order.status === "confirmed" && <ReservationList reservations={order.reservations} plan={plan} />}

      {/* Original input stays reachable after the review step */}
      {order.status !== "draft" && order.has_source && (
        <details className="bg-surface border border-line rounded-card">
          <summary className="px-5 py-3 text-sm font-medium cursor-pointer">{t("review.original")}</summary>
          <SourceViewer orderId={order.id} />
        </details>
      )}

      <AuditTrail logs={order.audit_logs} />

      {order.status === "draft" && (
        <div>
          <Button variant="ghost" disabled={busy} onClick={() => run(() => cancelOrder(order.id), t("order.cancelDone"))}>
            {t("order.cancel")}
          </Button>
        </div>
      )}
    </div>
  );
}
