import { useState, useMemo } from "react";
import { useSearchParams } from "react-router";
import {
  Truck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  MapPin,
  Calendar,
  Building2,
  Check,
  RotateCw,
  GitMerge,
  Package,
} from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { MockDataBanner } from "../components/ui/MockDataBanner";
import { Card, CardHeader, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { CountryBadge } from "../components/ui/CountryBadge";
import { Collapsible } from "../components/ui/Collapsible";
import { useToast } from "../components/ui/useToast";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { formatIsoDate, formatWeightKg, formatNumber } from "../lib/format";
import { cn } from "../lib/cn";
import { MOCK_FULFILLMENT_PLANS } from "../mocks/plan";
import type { VehicleType } from "../types/api";

const VEHICLE_LABELS: Record<VehicleType, string> = {
  small_truck: "Small Truck (<3.5t)",
  heavy_truck: "Heavy Truck (18t)",
  crane_truck: "Crane Truck (Hiab 26t)",
};

export default function PlanPage() {
  const { t } = useI18n();
  const { pushToast } = useToast();
  const [searchParams] = useSearchParams();
  useDocumentTitle(t("plan.title"));

  const orderId = searchParams.get("orderId") || "ord-dk-1041";
  const initialPlan = MOCK_FULFILLMENT_PLANS[orderId] || MOCK_FULFILLMENT_PLANS["ord-dk-1041"];

  const [isConfirmed, setIsConfirmed] = useState(false);
  const [expandedShipments, setExpandedShipments] = useState<Record<string, boolean>>({
    "SHP-DK-01": true,
    "SHP-SE-02": true,
    "SHP-NO-03": true,
  });

  const toggleShipmentExpand = (id: string) => {
    setExpandedShipments((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const plan = useMemo(() => initialPlan, [initialPlan]);

  const handleConfirmPlan = () => {
    setIsConfirmed(true);
    pushToast({
      title: "Plan Locked & Reserved",
      description: "ERP reservations created across DK/SE/NO systems.",
      tone: "success",
    });
  };

  const handleRecompute = () => {
    pushToast({
      title: "Optimizer Refreshed",
      description: "Dispatch algorithm re-evaluated stock across 8 warehouses.",
      tone: "info",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("plan.title")}
        subtitle={t("plan.subtitle")}
        actions={
          <div className="flex items-center gap-2.5">
            <Button variant="secondary" onClick={handleRecompute}>
              <RotateCw className="w-3.5 h-3.5 mr-1.5" />
              Re-optimize
            </Button>
            {!isConfirmed ? (
              <Button variant="primary" onClick={handleConfirmPlan}>
                <Check className="w-4 h-4 mr-1.5" />
                {t("plan.confirmPlanBtn")}
              </Button>
            ) : (
              <Badge tone="success" className="px-3 py-1 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {t("plan.planConfirmedBadge")}
              </Badge>
            )}
          </div>
        }
      />

      <MockDataBanner />

      {/* Order Summary Strip */}
      <Card>
        <CardBody className="p-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <h2 className="text-base font-bold text-ink">{plan.customer}</h2>
                <Badge tone={isConfirmed ? "success" : "brand"}>
                  {isConfirmed ? "CONFIRMED & RESERVED" : "OPTIMIZED PLAN"}
                </Badge>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-ink-muted">
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-brand" />
                  {plan.delivery_site}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-brand" />
                  {t("plan.contractorDate")}:{" "}
                  <strong className="text-ink font-mono">{formatIsoDate(plan.requested_date)}</strong>
                </span>
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs">
              <div>
                <p className="text-ink-muted uppercase font-semibold text-[10px]">
                  {t("plan.totalWeight")}
                </p>
                <p className="text-base font-bold text-ink font-mono mt-0.5">
                  {formatWeightKg(plan.total_weight_kg)}
                </p>
              </div>

              <div>
                <p className="text-ink-muted uppercase font-semibold text-[10px]">
                  {t("plan.totalShipments")}
                </p>
                <p className="text-base font-bold text-brand font-mono mt-0.5">
                  {plan.shipments.length}
                </p>
              </div>

              <div>
                <p className="text-ink-muted uppercase font-semibold text-[10px]">
                  Safe Commitment (P90)
                </p>
                <p className={cn("text-base font-bold font-mono mt-0.5", plan.on_time ? "text-success" : "text-warn")}>
                  {formatIsoDate(plan.max_p90_date)}
                </p>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Sourcing Hierarchy Visual Strip */}
      <div className="bg-surface p-4 rounded-xl border border-line flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-ink-muted">
          <GitMerge className="w-4 h-4 text-brand shrink-0" />
          <span className="font-semibold text-ink">Dispatch Hierarchy:</span>
          <span>{t("plan.hierarchyStrip")}</span>
        </div>
        <span className="font-mono text-[11px] text-ink-faint">Rule Engine v2.4</span>
      </div>

      {/* Shipment Cards List */}
      <div className="space-y-4">
        {plan.shipments.map((shipment) => {
          const isExpanded = !!expandedShipments[shipment.id];

          return (
            <Card key={shipment.id} className="overflow-hidden">
              <CardHeader className="py-4 bg-surface-2/40">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 w-full">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono font-bold text-sm text-ink bg-surface px-2.5 py-0.5 rounded border border-line">
                        {shipment.id}
                      </span>
                      <CountryBadge country={shipment.origin_country} />
                      <h3 className="text-sm font-bold text-ink">{shipment.origin_warehouse}</h3>
                      <Badge tone={shipment.on_time ? "success" : "warn"}>
                        {shipment.on_time ? t("plan.onTimeBadge") : t("plan.riskBadge")}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-ink-muted pt-1">
                      <span className="flex items-center gap-1 font-mono">
                        <MapPin className="w-3.5 h-3.5 text-brand" />
                        {shipment.distance_km} km
                      </span>
                      <span>•</span>
                      <span className="font-mono">{formatWeightKg(shipment.total_weight_kg)}</span>
                      <span>•</span>
                      <span>{shipment.lines.length} material lines</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge tone="neutral">{VEHICLE_LABELS[shipment.vehicle_type]}</Badge>
                    {shipment.crane_required && (
                      <Badge tone="warn">{t("plan.craneRequired")}</Badge>
                    )}
                    {shipment.cross_border && (
                      <Badge tone="info">{t("plan.crossBorder")}</Badge>
                    )}
                    <button
                      type="button"
                      onClick={() => toggleShipmentExpand(shipment.id)}
                      className="p-1 rounded text-ink-muted hover:text-ink hover:bg-surface-2 transition-colors ml-2 cursor-pointer"
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </CardHeader>

              <CardBody className="p-5 space-y-4">
                {/* Side-by-side ETA & Reasoning Block */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                  {/* ML ETA Comparison Box */}
                  <div className="md:col-span-5 p-4 rounded-xl bg-surface-2 border border-line space-y-3">
                    <div className="flex items-center justify-between text-xs pb-2 border-b border-line">
                      <span className="font-semibold text-ink flex items-center gap-1.5">
                        <Truck className="w-3.5 h-3.5 text-brand" />
                        {t("plan.etaComparison")}
                      </span>
                      <span className="font-mono text-[10px] text-ink-muted">Quantile Regression</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <p className="text-ink-muted text-[11px]">{t("plan.expectedP50")}</p>
                        <p className="text-sm font-bold font-mono text-ink mt-0.5">
                          {formatIsoDate(shipment.p50_date)}
                        </p>
                      </div>
                      <div>
                        <p className="text-ink-muted text-[11px]">{t("plan.safeCommitmentP90")}</p>
                        <p className={cn("text-sm font-bold font-mono mt-0.5", shipment.on_time ? "text-success" : "text-warn")}>
                          {formatIsoDate(shipment.p90_date)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Rule Reasoning Box */}
                  <div className="md:col-span-7 p-4 rounded-xl bg-brand-soft/30 border border-brand/20 space-y-2">
                    <p className="text-xs font-bold text-brand-ink">
                      {t("plan.ruleReasoning")}
                    </p>
                    <p className="text-xs text-ink leading-relaxed">
                      {shipment.selection_reason}
                    </p>
                    {isConfirmed && shipment.erp_reservation_id && (
                      <div className="pt-2 border-t border-brand/20 flex items-center gap-2 text-xs">
                        <span className="text-brand-ink font-semibold">{t("plan.erpRef")}:</span>
                        <span className="font-mono px-2 py-0.5 rounded bg-surface border border-line text-ink font-bold">
                          {shipment.erp_reservation_id}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Collapsible Shipment Items Table */}
                <Collapsible open={isExpanded}>
                  <div className="pt-2">
                    <div className="text-xs font-semibold text-ink-muted mb-2 flex items-center gap-1.5">
                      <Package className="w-3.5 h-3.5" />
                      <span>{t("plan.allocatedLines")}</span>
                    </div>
                    <div className="overflow-x-auto rounded-lg border border-line">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-surface-2 border-b border-line text-ink-muted font-semibold">
                            <th className="py-2 px-3 w-44">SKU</th>
                            <th className="py-2 px-3">Description</th>
                            <th className="py-2 px-3 w-28 text-right">Quantity</th>
                            <th className="py-2 px-3 w-28 text-right">Weight</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line">
                          {shipment.lines.map((line) => (
                            <tr key={line.sku} className="hover:bg-surface-2/30">
                              <td className="py-2.5 px-3 font-mono font-bold text-ink">
                                {line.sku}
                              </td>
                              <td className="py-2.5 px-3 text-ink">
                                {line.description}
                              </td>
                              <td className="py-2.5 px-3 text-right font-mono">
                                {formatNumber(line.quantity)} {line.unit}
                              </td>
                              <td className="py-2.5 px-3 text-right font-mono text-ink-muted">
                                {formatWeightKg(line.weight_kg)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </Collapsible>
              </CardBody>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
