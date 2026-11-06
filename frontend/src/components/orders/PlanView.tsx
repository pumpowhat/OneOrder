import { AlertTriangle, ArrowRight, Truck } from "lucide-react";
import { getModelInfo } from "../../api/stock.ts";
import { useApi } from "../../hooks/useApi.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { formatIsoDate, formatQty, formatWeightKg } from "../../lib/format.ts";
import { VEHICLE_LABEL } from "../../lib/status.ts";
import type { FulfillmentPlan } from "../../types/api.ts";
import { Badge } from "../ui/Badge.tsx";
import { Card, CardBody, CardHeader } from "../ui/Card.tsx";
import { CountryBadge } from "../ui/CountryBadge.tsx";
import { RiskBadge } from "./StatusBadge.tsx";

function ModelNote() {
  const { t } = useI18n();
  const { data } = useApi((signal) => getModelInfo(signal), []);
  return (
    <details className="text-xs text-ink-muted">
      <summary className="cursor-pointer hover:text-ink">{t("plan.aboutEta")}</summary>
      <div className="mt-2 space-y-1">
        <p>{t("plan.etaExplain")}</p>
        {data && (
          <p>
            {t("plan.etaMetrics", { cov: Math.round(data.metrics.p90_coverage * 100), rows: data.training_rows })}
          </p>
        )}
        {data && <p className="italic">{data.disclaimer}</p>}
      </div>
    </details>
  );
}

/** Where the goods come from, how they travel and when they should arrive (P50 expected, P90 safe). */
export function PlanView({ plan }: { plan: FulfillmentPlan }) {
  const { t } = useI18n();
  const eta = plan.order_eta;

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs text-ink-muted">{t("plan.deliverTo")}</div>
              <div className="text-sm font-medium flex items-center gap-2">
                {plan.site.name} <CountryBadge country={plan.site.country} />
              </div>
              {plan.site.match === "city" && <div className="text-xs text-warn mt-1">{t("plan.cityOnly")}</div>}
            </div>
            {eta && (
              <div className="flex flex-wrap items-center gap-6">
                <div>
                  <div className="text-xs text-ink-muted">{t("plan.expected")}</div>
                  <div className="text-xl font-semibold tabular-nums">{formatIsoDate(eta.p50_date)}</div>
                </div>
                <div>
                  <div className="text-xs text-ink-muted">{t("plan.safe")}</div>
                  <div className="text-xl font-semibold tabular-nums">{formatIsoDate(eta.p90_date)}</div>
                </div>
                <div>
                  <div className="text-xs text-ink-muted">{t("common.requestedDate")}</div>
                  <div className="text-sm font-medium tabular-nums flex items-center gap-2">
                    {formatIsoDate(plan.requested_date)} <RiskBadge risk={eta.risk} />
                  </div>
                </div>
              </div>
            )}
          </div>
          <ModelNote />
        </CardBody>
      </Card>

      {plan.shortages.length > 0 && (
        <div role="alert" className="rounded-card border border-danger/30 bg-danger-soft px-5 py-4 space-y-1.5">
          <div className="flex items-center gap-2 text-sm font-semibold text-danger">
            <AlertTriangle className="w-4 h-4" aria-hidden="true" />
            {t("plan.shortages")}
          </div>
          <ul className="text-sm text-danger space-y-0.5">
            {plan.shortages.map((s) => (
              <li key={`${s.line_index}-${s.sku}`}>
                {s.description ?? s.sku}: {t("plan.missing", { n: formatQty(s.missing) })}
              </li>
            ))}
          </ul>
        </div>
      )}

      {plan.warnings.length > 0 && (
        <ul className="rounded-card border border-warn/30 bg-warn-soft px-5 py-3 text-sm text-warn space-y-0.5">
          {plan.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {plan.shipments.map((s) => (
        <Card key={s.shipment_index}>
          <CardHeader className="flex-wrap gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <span className="text-sm font-semibold">{t("plan.shipment", { n: s.shipment_index })}</span>
              <CountryBadge country={s.origin_country} />
              <span className="text-sm truncate">{s.origin_name}</span>
              <ArrowRight className="w-3.5 h-3.5 text-ink-faint shrink-0" aria-hidden="true" />
              <CountryBadge country={s.destination_country} />
              {s.cross_border && <Badge tone="info">{t("plan.crossBorder")}</Badge>}
            </div>
            {s.eta && (
              <div className="flex items-center gap-2 text-sm tabular-nums">
                <span>{formatIsoDate(s.eta.p50_date)}</span>
                <span className="text-ink-faint">→</span>
                <span className="text-ink-muted">{formatIsoDate(s.eta.p90_date)}</span>
                <RiskBadge risk={s.eta.risk} />
              </div>
            )}
          </CardHeader>
          <CardBody className="space-y-3">
            <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-ink-muted">
              <span className="inline-flex items-center gap-1.5">
                <Truck className="w-3.5 h-3.5" aria-hidden="true" />
                {t(VEHICLE_LABEL[s.vehicle_type])}
                {s.vehicle_count > 1 && ` × ${s.vehicle_count}`}
              </span>
              <span>{Math.round(s.distance_km)} km</span>
              <span>{formatWeightKg(Math.round(s.total_weight_kg))}</span>
              {s.crane_required && <span>{t("plan.crane")}</span>}
            </div>
            <ul className="text-sm divide-y divide-line">
              {s.lines.map((a) => (
                <li key={`${a.line_index}-${a.sku}`} className="py-1.5 flex items-baseline justify-between gap-4">
                  <span className="min-w-0 truncate">{a.description ?? a.sku}</span>
                  <span className="tabular-nums text-ink-muted shrink-0">
                    {formatQty(a.quantity)} {a.unit}
                  </span>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
