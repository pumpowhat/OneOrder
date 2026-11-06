import { useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { getRules, saveRules } from "../api/rules.ts";
import { useApi } from "../hooks/useApi.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";
import type { TranslationKey } from "../i18n/en.ts";
import { errorMessage } from "../lib/errors.ts";
import { VEHICLE_LABEL } from "../lib/status.ts";
import type { Rules, SourcingTier } from "../types/api.ts";
import { Button } from "../components/ui/Button.tsx";
import { Card, CardBody, CardHeader } from "../components/ui/Card.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";
import { useToast } from "../components/ui/useToast.ts";

const TIER_LABEL: Record<SourcingTier, TranslationKey> = {
  branch: "rules.tier.branch",
  domestic_dc: "rules.tier.domestic_dc",
  cross_border_dc: "rules.tier.cross_border_dc",
};

function Toggle({ label, hint, checked, onChange }: { label: string; hint: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="mt-1 w-4 h-4 accent-[var(--brand)]" />
      <span>
        <span className="block text-sm font-medium">{label}</span>
        <span className="block text-xs text-ink-muted">{hint}</span>
      </span>
    </label>
  );
}

function NumberField({ label, hint, value, min, step, onChange }: { label: string; hint: string; value: number; min: number; step?: number; onChange: (v: number) => void }) {
  return (
    <label className="block space-y-1">
      <span className="block text-sm font-medium">{label}</span>
      <input
        type="number"
        min={min}
        step={step ?? 1}
        value={Number.isFinite(value) ? value : ""}
        onChange={(e) => onChange(e.target.value === "" ? Number.NaN : Number(e.target.value))}
        className="w-32 h-9 px-2 rounded-md border border-line-strong bg-surface text-sm tabular-nums"
      />
      <span className="block text-xs text-ink-muted">{hint}</span>
    </label>
  );
}

export default function RulesPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.rules"));
  const { pushToast } = useToast();
  const { data, error, loading, reload } = useApi((signal) => getRules(signal), []);
  const [draft, setDraft] = useState<Rules | null>(null);
  const [saving, setSaving] = useState(false);

  const rules = draft ?? data;
  if (loading && !rules) return <p className="text-sm text-ink-muted">{t("common.loading")}</p>;
  if (error || !rules) {
    return <p className="text-sm text-danger">{error ? errorMessage(error, t) : t("common.loading")}</p>;
  }

  const set = (patch: (r: Rules) => Rules) => setDraft(patch(rules));
  const move = (index: number, delta: number) =>
    set((r) => {
      const priority = [...r.sourcing.priority];
      const target = index + delta;
      if (target < 0 || target >= priority.length) return r;
      [priority[index], priority[target]] = [priority[target], priority[index]];
      return { ...r, sourcing: { ...r.sourcing, priority } };
    });

  const valid =
    rules.sourcing.branch_max_distance_km > 0 &&
    rules.sourcing.max_shipments_per_order >= 1 &&
    rules.distance.road_factor >= 1 &&
    rules.vehicles.every((v) => v.max_weight_kg > 0);

  const save = async () => {
    setSaving(true);
    try {
      const saved = await saveRules(rules);
      setDraft(null);
      reload();
      pushToast({ tone: "success", title: t("rules.saved", { v: saved.version }) });
    } catch (err) {
      pushToast({ tone: "danger", title: t("error.actionFailed"), description: errorMessage(err, t) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("nav.rules")}
        subtitle={t("rules.subtitle", { v: rules.version })}
        actions={
          <>
            {draft && (
              <Button variant="ghost" disabled={saving} onClick={() => setDraft(null)}>
                {t("common.reset")}
              </Button>
            )}
            <Button variant="accent" disabled={!draft || !valid || saving} onClick={() => void save()}>
              {saving ? t("common.working") : t("common.save")}
            </Button>
          </>
        }
      />

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold">{t("rules.sourcing")}</h2>
        </CardHeader>
        <CardBody className="space-y-6">
          <div className="space-y-2">
            <div className="text-sm font-medium">{t("rules.priority")}</div>
            <p className="text-xs text-ink-muted">{t("rules.priorityHint")}</p>
            <ol className="space-y-2 max-w-md">
              {rules.sourcing.priority.map((tier, i) => (
                <li key={tier} className="flex items-center gap-3 bg-surface-2 border border-line rounded-lg px-3 py-2">
                  <span className="w-5 text-xs font-semibold text-ink-muted tabular-nums">{i + 1}</span>
                  <span className="flex-1 text-sm">{t(TIER_LABEL[tier])}</span>
                  <button
                    type="button"
                    onClick={() => move(i, -1)}
                    disabled={i === 0}
                    aria-label={t("rules.moveUp", { name: t(TIER_LABEL[tier]) })}
                    className="p-1 rounded hover:bg-surface disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <ArrowUp className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => move(i, 1)}
                    disabled={i === rules.sourcing.priority.length - 1}
                    aria-label={t("rules.moveDown", { name: t(TIER_LABEL[tier]) })}
                    className="p-1 rounded hover:bg-surface disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <ArrowDown className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ol>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Toggle
              label={t("rules.crossBorder")}
              hint={t("rules.crossBorderHint")}
              checked={rules.sourcing.allow_cross_border}
              onChange={(v) => set((r) => ({ ...r, sourcing: { ...r.sourcing, allow_cross_border: v } }))}
            />
            <Toggle
              label={t("rules.lineSplit")}
              hint={t("rules.lineSplitHint")}
              checked={rules.sourcing.allow_line_split}
              onChange={(v) => set((r) => ({ ...r, sourcing: { ...r.sourcing, allow_line_split: v } }))}
            />
            <NumberField
              label={t("rules.branchRadius")}
              hint={t("rules.branchRadiusHint")}
              value={rules.sourcing.branch_max_distance_km}
              min={1}
              onChange={(v) => set((r) => ({ ...r, sourcing: { ...r.sourcing, branch_max_distance_km: v } }))}
            />
            <NumberField
              label={t("rules.maxShipments")}
              hint={t("rules.maxShipmentsHint")}
              value={rules.sourcing.max_shipments_per_order}
              min={1}
              onChange={(v) => set((r) => ({ ...r, sourcing: { ...r.sourcing, max_shipments_per_order: v } }))}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold">{t("rules.transport")}</h2>
        </CardHeader>
        <CardBody className="space-y-6">
          <NumberField
            label={t("rules.roadFactor")}
            hint={t("rules.roadFactorHint")}
            value={rules.distance.road_factor}
            min={1}
            step={0.05}
            onChange={(v) => set((r) => ({ ...r, distance: { ...r.distance, road_factor: v } }))}
          />
          <div className="space-y-2">
            <div className="text-sm font-medium">{t("rules.fleet")}</div>
            <ul className="space-y-2 max-w-md">
              {rules.vehicles.map((vehicle, i) => (
                <li key={vehicle.type} className="flex items-center gap-3">
                  <span className="flex-1 text-sm">{t(VEHICLE_LABEL[vehicle.type])}</span>
                  <input
                    type="number"
                    min={1}
                    value={Number.isFinite(vehicle.max_weight_kg) ? vehicle.max_weight_kg : ""}
                    aria-label={t("rules.vehicleWeight", { name: t(VEHICLE_LABEL[vehicle.type]) })}
                    onChange={(e) =>
                      set((r) => ({
                        ...r,
                        vehicles: r.vehicles.map((v, j) => (j === i ? { ...v, max_weight_kg: e.target.value === "" ? Number.NaN : Number(e.target.value) } : v)),
                      }))
                    }
                    className="w-28 h-9 px-2 rounded-md border border-line-strong bg-surface text-sm tabular-nums text-right"
                  />
                  <span className="text-xs text-ink-muted w-6">kg</span>
                </li>
              ))}
            </ul>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
