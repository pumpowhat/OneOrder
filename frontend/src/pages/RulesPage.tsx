import { useState } from "react";
import {
  Sliders,
  RotateCcw,
  Save,
  ShieldCheck,
  Truck,
  Globe,
  FileJson,
  Layers,
} from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { MockDataBanner } from "../components/ui/MockDataBanner";
import { Card, CardHeader, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { CountryBadge } from "../components/ui/CountryBadge";
import { useToast } from "../components/ui/useToast";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { DEFAULT_RULES, type RulesConfig } from "../mocks/rules";
import type { NordicCountry } from "../types/api";

export default function RulesPage() {
  const { t } = useI18n();
  const { pushToast } = useToast();
  useDocumentTitle(t("rules.title"));

  const [rules, setRules] = useState<RulesConfig>(DEFAULT_RULES);

  const handleReset = () => {
    setRules(DEFAULT_RULES);
    pushToast({
      title: "Rules Reset",
      description: "Restored all default dispatch and review thresholds.",
      tone: "info",
    });
  };

  const handleSave = () => {
    pushToast({
      title: "Rules Saved",
      description: t("rules.savedToast"),
      tone: "success",
    });
  };

  const updateMarketBuffer = (
    country: NordicCountry,
    field: "dcLeadDays" | "crossBorderExtraDays" | "winterPenaltyDays",
    value: number
  ) => {
    setRules((prev) => ({
      ...prev,
      marketBuffers: {
        ...prev.marketBuffers,
        [country]: {
          ...prev.marketBuffers[country],
          [field]: value,
        },
      },
    }));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("rules.title")}
        subtitle={t("rules.subtitle")}
        actions={
          <div className="flex items-center gap-2.5">
            <Button variant="secondary" onClick={handleReset}>
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              {t("rules.resetBtn")}
            </Button>
            <Button variant="primary" onClick={handleSave}>
              <Save className="w-3.5 h-3.5 mr-1.5" />
              {t("rules.saveBtn")}
            </Button>
          </div>
        }
      />

      <MockDataBanner />

      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Left Column: Editable Configuration Cards */}
        <div className="col-span-7 space-y-5">
          {/* 1. Intake Governance Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-ink">
                  {t("rules.intakeCardTitle")}
                </h3>
              </div>
            </CardHeader>
            <CardBody className="p-5 space-y-4">
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <label htmlFor="confidence-range" className="font-semibold text-ink">
                    {t("rules.confidenceThreshold")}
                  </label>
                  <span className="font-mono font-bold text-brand text-sm">
                    {Math.round(rules.intake.minConfidenceThreshold * 100)}%
                  </span>
                </div>
                <input
                  id="confidence-range"
                  type="range"
                  min="0.50"
                  max="0.99"
                  step="0.01"
                  value={rules.intake.minConfidenceThreshold}
                  onChange={(e) =>
                    setRules((prev) => ({
                      ...prev,
                      intake: {
                        ...prev.intake,
                        minConfidenceThreshold: parseFloat(e.target.value),
                      },
                    }))
                  }
                  className="w-full accent-brand cursor-pointer"
                />
                <p className="text-[11px] text-ink-muted mt-1">
                  Extracted lines below this threshold automatically trigger human verification.
                </p>
              </div>

              <div className="pt-3 border-t border-line flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-ink">
                    {t("rules.blockAmbiguous")}
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    Flag lines where multiple catalog candidates have close RapidFuzz scores.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={rules.intake.requireHumanConfirmOnAmbiguous}
                  onChange={(e) =>
                    setRules((prev) => ({
                      ...prev,
                      intake: {
                        ...prev.intake,
                        requireHumanConfirmOnAmbiguous: e.target.checked,
                      },
                    }))
                  }
                  className="w-4 h-4 accent-brand rounded cursor-pointer"
                />
              </div>

              <div className="pt-3 border-t border-line flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-ink">
                    RapidFuzz Matching Cutoff Score
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    Minimum catalog similarity score required to propose a match.
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    min="50"
                    max="100"
                    value={rules.intake.fuzzyMatchMinScore}
                    onChange={(e) =>
                      setRules((prev) => ({
                        ...prev,
                        intake: {
                          ...prev.intake,
                          fuzzyMatchMinScore: parseInt(e.target.value, 10) || 80,
                        },
                      }))
                    }
                    className="w-16 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                  />
                  <span className="text-xs text-ink-muted font-mono">/ 100</span>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* 2. Sourcing Hierarchy Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-ink">
                  {t("rules.sourcingCardTitle")}
                </h3>
              </div>
            </CardHeader>
            <CardBody className="p-5 space-y-4">
              <div>
                <p className="text-xs font-semibold text-ink mb-1.5">
                  {t("rules.priorityOrder")}
                </p>
                <div className="p-3 bg-surface-2 rounded-lg border border-line flex items-center gap-2 text-xs font-mono">
                  <span className="px-2 py-0.5 rounded bg-surface border border-line text-ink font-bold">
                    1. Nearest Branch
                  </span>
                  <span>→</span>
                  <span className="px-2 py-0.5 rounded bg-surface border border-line text-ink font-bold">
                    2. Domestic Central DC
                  </span>
                  <span>→</span>
                  <span className="px-2 py-0.5 rounded bg-surface border border-line text-brand-ink font-bold">
                    3. Cross-Border DC
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-line flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-ink">
                    {t("rules.crossBorderToggle")}
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    Fallback to SE or NO hubs when domestic branch and DC stock is depleted.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={rules.sourcing.allowCrossBorderFallback}
                  onChange={(e) =>
                    setRules((prev) => ({
                      ...prev,
                      sourcing: {
                        ...prev.sourcing,
                        allowCrossBorderFallback: e.target.checked,
                      },
                    }))
                  }
                  className="w-4 h-4 accent-brand rounded cursor-pointer"
                />
              </div>

              <div className="pt-3 border-t border-line flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-ink">
                    {t("rules.maxShipments")}
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    Prevent excessive split-shipment dispatch per contractor delivery site.
                  </p>
                </div>
                <input
                  type="number"
                  min="1"
                  max="6"
                  value={rules.sourcing.maxShipmentsPerOrder}
                  onChange={(e) =>
                    setRules((prev) => ({
                      ...prev,
                      sourcing: {
                        ...prev.sourcing,
                        maxShipmentsPerOrder: parseInt(e.target.value, 10) || 3,
                      },
                    }))
                  }
                  className="w-16 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                />
              </div>
            </CardBody>
          </Card>

          {/* 3. Vehicle & Crane Assignment Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-ink">
                  {t("rules.vehicleCardTitle")}
                </h3>
              </div>
            </CardHeader>
            <CardBody className="p-5 space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label htmlFor="small-truck-input" className="text-xs font-semibold text-ink block mb-1">
                    Small Truck
                  </label>
                  <div className="flex items-center gap-1">
                    <input
                      id="small-truck-input"
                      type="number"
                      step="100"
                      value={rules.vehicles.smallTruckMaxKg}
                      onChange={(e) =>
                        setRules((prev) => ({
                          ...prev,
                          vehicles: {
                            ...prev.vehicles,
                            smallTruckMaxKg: parseInt(e.target.value, 10) || 1500,
                          },
                        }))
                      }
                      className="w-full h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                    />
                    <span className="text-xs text-ink-muted font-mono">kg</span>
                  </div>
                </div>

                <div>
                  <label htmlFor="heavy-truck-input" className="text-xs font-semibold text-ink block mb-1">
                    Heavy Truck
                  </label>
                  <div className="flex items-center gap-1">
                    <input
                      id="heavy-truck-input"
                      type="number"
                      step="500"
                      value={rules.vehicles.heavyTruckMaxKg}
                      onChange={(e) =>
                        setRules((prev) => ({
                          ...prev,
                          vehicles: {
                            ...prev.vehicles,
                            heavyTruckMaxKg: parseInt(e.target.value, 10) || 12000,
                          },
                        }))
                      }
                      className="w-full h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                    />
                    <span className="text-xs text-ink-muted font-mono">kg</span>
                  </div>
                </div>

                <div>
                  <label htmlFor="crane-truck-input" className="text-xs font-semibold text-ink block mb-1">
                    Crane Truck
                  </label>
                  <div className="flex items-center gap-1">
                    <input
                      id="crane-truck-input"
                      type="number"
                      step="500"
                      value={rules.vehicles.craneTruckMaxKg}
                      onChange={(e) =>
                        setRules((prev) => ({
                          ...prev,
                          vehicles: {
                            ...prev.vehicles,
                            craneTruckMaxKg: parseInt(e.target.value, 10) || 18000,
                          },
                        }))
                      }
                      className="w-full h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                    />
                    <span className="text-xs text-ink-muted font-mono">kg</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-line flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-ink">
                    {t("rules.autoCraneToggle")}
                  </p>
                  <p className="text-[11px] text-ink-muted">
                    Auto-enforce Hiab crane truck when steel beams or heavy panels are included.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={rules.vehicles.autoAssignCraneForFlaggedSku}
                  onChange={(e) =>
                    setRules((prev) => ({
                      ...prev,
                      vehicles: {
                        ...prev.vehicles,
                        autoAssignCraneForFlaggedSku: e.target.checked,
                      },
                    }))
                  }
                  className="w-4 h-4 accent-brand rounded cursor-pointer"
                />
              </div>
            </CardBody>
          </Card>

          {/* 4. Nordic Market Buffers Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-brand" />
                <h3 className="text-sm font-bold text-ink">
                  {t("rules.buffersCardTitle")}
                </h3>
              </div>
            </CardHeader>
            <CardBody className="p-0 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-line text-ink-muted font-semibold">
                    <th className="py-2.5 px-4 w-28">Market</th>
                    <th className="py-2.5 px-3 text-right">DC Lead (Days)</th>
                    <th className="py-2.5 px-3 text-right">Cross-Border Buffer</th>
                    <th className="py-2.5 px-4 text-right">Winter Weather Penalty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {(["DK", "SE", "NO"] as NordicCountry[]).map((country) => {
                    const buf = rules.marketBuffers[country];

                    return (
                      <tr key={country} className="hover:bg-surface-2/30">
                        <td className="py-3 px-4 font-semibold text-ink flex items-center gap-2">
                          <CountryBadge country={country} />
                          <span>
                            {country === "DK" ? "Denmark" : country === "SE" ? "Sweden" : "Norway"}
                          </span>
                        </td>

                        <td className="py-3 px-3 text-right">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={buf.dcLeadDays}
                            onChange={(e) =>
                              updateMarketBuffer(country, "dcLeadDays", parseFloat(e.target.value) || 0)
                            }
                            className="w-16 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                          />
                        </td>

                        <td className="py-3 px-3 text-right">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={buf.crossBorderExtraDays}
                            onChange={(e) =>
                              updateMarketBuffer(country, "crossBorderExtraDays", parseFloat(e.target.value) || 0)
                            }
                            className="w-16 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                          />
                        </td>

                        <td className="py-3 px-4 text-right">
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={buf.winterPenaltyDays}
                            onChange={(e) =>
                              updateMarketBuffer(country, "winterPenaltyDays", parseFloat(e.target.value) || 0)
                            }
                            className="w-16 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink text-right focus:outline-brand"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardBody>
          </Card>
        </div>

        {/* Right Column: Sticky Live rules.json Preview */}
        <div className="col-span-5 sticky top-20 space-y-4">
          <Card>
            <CardHeader className="py-3.5 bg-surface-2/40">
              <div className="flex items-center gap-2">
                <FileJson className="w-4 h-4 text-brand" />
                <div>
                  <h3 className="text-xs font-bold text-ink">
                    {t("rules.livePreviewTitle")}
                  </h3>
                  <p className="text-[10px] text-ink-muted">
                    {t("rules.livePreviewSubtitle")}
                  </p>
                </div>
              </div>
              <span className="font-mono text-[10px] bg-brand-soft text-brand-ink px-2 py-0.5 rounded border border-brand/20">
                Live State
              </span>
            </CardHeader>

            <CardBody className="p-4">
              <pre className="bg-surface-2 p-3.5 rounded-lg border border-line font-mono text-[11px] text-ink leading-relaxed overflow-x-auto max-h-[580px] select-text">
                {JSON.stringify(rules, null, 2)}
              </pre>
            </CardBody>
          </Card>

          <div className="p-3.5 rounded-lg bg-surface-2 border border-line text-xs text-ink-muted flex items-start gap-2.5">
            <Sliders className="w-4 h-4 text-brand shrink-0 mt-0.5" />
            <p>
              Changes are reflected in the live JSON buffer. Clicking <strong>Save Rules</strong> commits the configuration into the backend optimization pipeline.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
