import { useI18n } from "../../i18n/useI18n.ts";
import { formatQty } from "../../lib/format.ts";
import type { FulfillmentPlan, NordicCountry, Reservation } from "../../types/api.ts";
import { CountryBadge } from "../ui/CountryBadge.tsx";

/** What was written into each country's ERP when the order was confirmed. */
export function ReservationList({ reservations, plan }: { reservations: Reservation[]; plan: FulfillmentPlan | null }) {
  const { t } = useI18n();
  if (reservations.length === 0) return null;

  const warehouseName = new Map(plan?.shipments.map((s) => [s.origin_warehouse, s.origin_name]));
  const itemName = new Map(plan?.shipments.flatMap((s) => s.lines.map((a) => [a.sku, a.description ?? a.sku] as const)));

  return (
    <details className="bg-surface border border-line rounded-card">
      <summary className="px-5 py-3 text-sm font-medium cursor-pointer">
        {t("reservations.title")} <span className="text-ink-muted font-normal">({reservations.length})</span>
      </summary>
      <table className="w-full text-sm border-t border-line">
        <thead>
          <tr className="text-left text-xs text-ink-muted bg-surface-2">
            <th className="px-5 py-2 font-medium">{t("reservations.erp")}</th>
            <th className="px-3 py-2 font-medium">{t("stock.warehouse")}</th>
            <th className="px-3 py-2 font-medium">{t("stock.item")}</th>
            <th className="px-5 py-2 font-medium text-right">{t("reservations.qty")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {reservations.map((r, i) => (
            <tr key={`${r.warehouse_code}-${r.sku}-${i}`}>
              <td className="px-5 py-2">
                <CountryBadge country={r.warehouse_code.split("-")[0] as NordicCountry} />
              </td>
              <td className="px-3 py-2">
                {warehouseName.get(r.warehouse_code) ?? r.warehouse_code}
                <span className="ml-2 font-mono text-xs text-ink-faint">{r.warehouse_code}</span>
              </td>
              <td className="px-3 py-2">
                {itemName.get(r.sku) ?? r.sku}
                <span className="ml-2 font-mono text-xs text-info">{r.sku}</span>
              </td>
              <td className="px-5 py-2 text-right tabular-nums">
                {formatQty(r.quantity)} {r.unit}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
