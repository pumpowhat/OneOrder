import { useState, useMemo } from "react";
import {
  Activity,
  Cpu,
  ShieldCheck,
  Sliders,
  TrendingUp,
  BarChart2,
  Sparkles,
  Info,
  Calendar,
} from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { MockDataBanner } from "../components/ui/MockDataBanner";
import { Card, CardHeader, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Segmented } from "../components/ui/Segmented";
import { useToast } from "../components/ui/useToast";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { formatPercent } from "../lib/format";
import { MOCK_MODEL_DATA } from "../mocks/model";
import type { WarehouseSourceType } from "../types/api";

export default function ModelPage() {
  const { t } = useI18n();
  const { pushToast } = useToast();
  useDocumentTitle(t("model.title"));

  // What-If Simulator state
  const [simDistance, setSimDistance] = useState<number>(180);
  const [simSourceType, setSimSourceType] = useState<WarehouseSourceType>("domestic_dc");
  const [simCrossBorder, setSimCrossBorder] = useState<boolean>(false);
  const [simCrane, setSimCrane] = useState<boolean>(false);
  const [simWinter, setSimWinter] = useState<boolean>(true);

  // Compute simulated P50 and P90 dynamically
  const simulation = useMemo(() => {
    let baseDays = 0.5;
    if (simSourceType === "domestic_dc") baseDays = 1.0;
    if (simSourceType === "cross_border_dc") baseDays = 2.0;

    const distanceDays = simDistance / 350;
    const borderDays = simCrossBorder || simSourceType === "cross_border_dc" ? 1.0 : 0;
    const craneDays = simCrane ? 0.6 : 0;
    const winterDays = simWinter ? 0.5 : 0;

    const rawP50 = baseDays + distanceDays + borderDays + craneDays + winterDays;
    const p50 = Math.max(1, Math.round(rawP50 * 10) / 10);
    const riskFactor = simCrossBorder ? 0.8 : 0.4;
    const weatherRisk = simWinter ? 0.5 : 0.2;
    const p90 = Math.round((p50 * 1.35 + riskFactor + weatherRisk) * 10) / 10;
    const buffer = Math.round((p90 - p50) * 10) / 10;

    return { p50, p90, buffer };
  }, [simDistance, simSourceType, simCrossBorder, simCrane, simWinter]);

  const handleRetrain = () => {
    pushToast({
      title: "Model Retraining Scheduled",
      description: "Batch retraining triggered across 12,500 historical Nordic shipments.",
      tone: "info",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("model.title")}
        subtitle={t("model.subtitle")}
        actions={
          <Button variant="secondary" onClick={handleRetrain}>
            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-brand" />
            Retrain Model (Demo)
          </Button>
        }
      />

      <MockDataBanner />

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("model.kpiP50Mae")}</p>
              <p className="text-2xl font-bold font-mono text-ink mt-1">
                {MOCK_MODEL_DATA.p50MaeDays} <span className="text-sm font-normal text-ink-muted">days</span>
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-success-soft text-success flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("model.kpiP90Coverage")}</p>
              <p className="text-2xl font-bold font-mono text-brand mt-1">
                {formatPercent(MOCK_MODEL_DATA.p90EmpiricalCoverage)}
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("model.kpiSamples")}</p>
              <p className="text-xl font-bold font-mono text-ink mt-1">
                12,500 <span className="text-xs font-normal text-ink-muted">shipments</span>
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("model.kpiLossAlpha")}</p>
              <p className="text-sm font-bold font-mono text-ink mt-1.5">
                Pinball α = 0.50 / 0.90
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center">
              <BarChart2 className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Main Grid: Feature Importance on Left, Simulator on Right */}
      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Left Column: 8 Feature Importance Bars */}
        <div className="col-span-6 space-y-6">
          <Card>
            <CardHeader>
              <div>
                <h3 className="text-sm font-bold text-ink">
                  {t("model.featureChartTitle")}
                </h3>
                <p className="text-xs text-ink-muted">
                  {t("model.featureChartSubtitle")}
                </p>
              </div>
              <Badge tone="brand">Normalized (1.00)</Badge>
            </CardHeader>

            <CardBody className="p-5 space-y-4">
              {MOCK_MODEL_DATA.features.map((feat) => {
                const percentStr = `${Math.round(feat.importance * 100)}%`;

                return (
                  <div key={feat.key} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-ink">{feat.name}</span>
                        <span className="font-mono text-[10px] text-ink-muted ml-2">
                          ({feat.key})
                        </span>
                      </div>
                      <span className="font-mono font-bold text-brand">{percentStr}</span>
                    </div>

                    {/* CSS Progress Bar */}
                    <div className="w-full h-2 rounded-full bg-surface-2 overflow-hidden border border-line">
                      <div
                        className="h-full rounded-full bg-brand transition-all duration-300"
                        style={{ width: percentStr }}
                      />
                    </div>

                    <p className="text-[11px] text-ink-muted">{feat.description}</p>
                  </div>
                );
              })}
            </CardBody>
          </Card>
        </div>

        {/* Right Column: Interactive What-If ETA Simulator & Calibration */}
        <div className="col-span-6 space-y-6">
          {/* Interactive What-If Simulator Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-brand" />
                <div>
                  <h3 className="text-sm font-bold text-ink">
                    {t("model.simulatorTitle")}
                  </h3>
                  <p className="text-xs text-ink-muted">
                    {t("model.simulatorSubtitle")}
                  </p>
                </div>
              </div>
            </CardHeader>

            <CardBody className="p-5 space-y-5">
              {/* Distance Slider */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <label htmlFor="sim-distance-range" className="font-semibold text-ink">
                    {t("model.simDistance")}
                  </label>
                  <span className="font-mono font-bold text-brand text-sm">
                    {simDistance} km
                  </span>
                </div>
                <input
                  id="sim-distance-range"
                  type="range"
                  min="10"
                  max="800"
                  step="10"
                  value={simDistance}
                  onChange={(e) => setSimDistance(parseInt(e.target.value, 10))}
                  className="w-full accent-brand cursor-pointer"
                />
              </div>

              {/* Source Warehouse Type */}
              <div>
                <label className="text-xs font-semibold text-ink block mb-1.5">
                  {t("model.simSourceType")}
                </label>
                <Segmented<WarehouseSourceType>
                  size="sm"
                  value={simSourceType}
                  onChange={setSimSourceType}
                  options={[
                    { value: "branch", label: "Local Branch" },
                    { value: "domestic_dc", label: "Domestic DC" },
                    { value: "cross_border_dc", label: "Cross-Border DC" },
                  ]}
                />
              </div>

              {/* Toggles */}
              <div className="pt-3 border-t border-line space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-ink">
                      {t("model.simCrossBorder")}
                    </p>
                    <p className="text-[11px] text-ink-muted">
                      Transit crosses Øresund Bridge or Svinesund toll
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={simCrossBorder || simSourceType === "cross_border_dc"}
                    disabled={simSourceType === "cross_border_dc"}
                    onChange={(e) => setSimCrossBorder(e.target.checked)}
                    className="w-4 h-4 accent-brand rounded cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-ink">
                      {t("model.simCrane")}
                    </p>
                    <p className="text-[11px] text-ink-muted">
                      Allocates specialized crane truck with loading buffer
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={simCrane}
                    onChange={(e) => setSimCrane(e.target.checked)}
                    className="w-4 h-4 accent-brand rounded cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-ink">
                      {t("model.simWinter")}
                    </p>
                    <p className="text-[11px] text-ink-muted">
                      Seasonal weather disruption factor active (Nov–Mar)
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={simWinter}
                    onChange={(e) => setSimWinter(e.target.checked)}
                    className="w-4 h-4 accent-brand rounded cursor-pointer"
                  />
                </div>
              </div>

              {/* Live Prediction Display */}
              <div className="p-4 rounded-xl bg-surface-2 border border-line space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-ink pb-2 border-b border-line">
                  <span className="flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-brand" />
                    Simulated Quantile Outputs
                  </span>
                  <span className="font-mono text-[10px] text-ink-muted">Dynamic inference</span>
                </div>

                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-2.5 rounded-lg bg-surface border border-line">
                    <p className="text-[11px] text-ink-muted">{t("model.simP50")}</p>
                    <p className="text-lg font-bold font-mono text-ink mt-0.5">
                      {simulation.p50} <span className="text-xs font-normal">days</span>
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-surface border border-brand/30">
                    <p className="text-[11px] text-brand-ink font-semibold">{t("model.simP90")}</p>
                    <p className="text-lg font-bold font-mono text-brand mt-0.5">
                      {simulation.p90} <span className="text-xs font-normal">days</span>
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-surface border border-line">
                    <p className="text-[11px] text-ink-muted">{t("model.simBuffer")}</p>
                    <p className="text-lg font-bold font-mono text-warn mt-0.5">
                      +{simulation.buffer} <span className="text-xs font-normal">days</span>
                    </p>
                  </div>
                </div>

                {/* Timeline Comparison Bar */}
                <div className="pt-2">
                  <div className="flex items-center justify-between text-[11px] font-mono text-ink-muted mb-1">
                    <span>Dispatch (Day 0)</span>
                    <span>P50: {simulation.p50}d</span>
                    <span className="text-brand font-semibold">P90 Commitment: {simulation.p90}d</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-surface border border-line overflow-hidden flex">
                    <div
                      className="h-full bg-brand/40"
                      style={{ width: `${Math.min(75, (simulation.p50 / simulation.p90) * 100)}%` }}
                    />
                    <div
                      className="h-full bg-brand"
                      style={{ width: `${Math.max(25, 100 - (simulation.p50 / simulation.p90) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Nordic Calibration & Transparency Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-ink">
                  {t("model.calibrationTitle")}
                </h3>
              </div>
              <span className="font-mono text-[10px] text-ink-muted">docs/eta-calibration.md</span>
            </CardHeader>
            <CardBody className="p-4 space-y-3 text-xs text-ink-muted leading-relaxed">
              <p>{MOCK_MODEL_DATA.calibrationNote}</p>
              <div className="p-3 bg-surface-2 rounded-lg border border-line flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1.5 font-medium text-ink">
                  <Calendar className="w-3.5 h-3.5 text-brand" />
                  Model Retrain Cycle: Weekly Automated
                </span>
                <span className="font-mono text-ink-faint">
                  Last: {MOCK_MODEL_DATA.lastTrained}
                </span>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
