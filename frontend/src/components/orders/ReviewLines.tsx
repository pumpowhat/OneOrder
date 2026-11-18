import { useState } from "react";
import { CustomerCandidates } from "./CustomerCandidates.tsx";
import { Button } from "../ui/Button.tsx";
import { Badge, type BadgeTone } from "../ui/Badge.tsx";
import { useI18n } from "../../i18n/useI18n.ts";
import type { TranslationKey } from "../../i18n/en.ts";
import { formatQty } from "../../lib/format.ts";
import { isValidCustomerPhone } from "../../lib/phone.ts";
import type {
  AvailabilityStatus,
  CustomerCandidate,
  LineAvailability,
  LineCorrection,
  Order,
} from "../../types/api.ts";

const AVAIL: Record<
  AvailabilityStatus,
  { tone: BadgeTone; label: TranslationKey }
> = {
  ok: { tone: "success", label: "avail.ok" },
  partial: { tone: "warn", label: "avail.partial" },
  none: { tone: "danger", label: "avail.none" },
  unmatched: { tone: "neutral", label: "avail.unmatched" },
};

/** Review saved data. Editing is handled by OrderDraftForm so approval never loses unsaved edits. */
export function ReviewLines({
  order,
  availability,
  busy,
  onApprove,
  onSelectCustomer,
  onManualCustomer,
}: {
  order: Order;
  availability: LineAvailability[];
  busy: boolean;
  onSelectCustomer: (candidate: CustomerCandidate) => void;
  onManualCustomer: () => void;
  onApprove: (
    corrections: LineCorrection[],
    confirmLines: number[],
    customer?: string,
    customerPhone?: string,
  ) => void;
}) {
  const { t } = useI18n();
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const missingCustomer = !order.customer?.trim();
  const invalidPhone = !isValidCustomerPhone(order.customer_phone ?? "");
  const pending = order.lines.filter(
    (l) => !l.matched_sku || (l.needs_review && !checked.has(l.line_index)),
  );
  return (
    <div>
      <p className="px-5 py-4 text-sm text-ink-muted border-b border-line">
        {t("draft.reviewHint")}
      </p>
      <div className="px-5 empty:hidden [&:not(:empty)]:pt-4">
        <CustomerCandidates
          orderId={order.id}
          key={JSON.stringify([order.customer, order.customer_phone])}
          link={{
            crm_account_id: order.crm_account_id ?? null,
            crm_contact_id: order.crm_contact_id ?? null,
          }}
          disabled={busy}
          onSelect={onSelectCustomer}
          onManual={onManualCustomer}
        />
      </div>
      {order.lines.length === 0 && (
        <p className="px-5 py-6 text-sm text-ink-muted">{t("draft.empty")}</p>
      )}
      <ul className="divide-y divide-line">
        {order.lines.map((line) => {
          const avail = availability.find(
            (a) => a.line_index === line.line_index,
          );
          return (
            <li key={line.line_index} className="px-5 py-5 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-1">
                  <div className="font-medium text-sm break-words">
                    {line.description}
                  </div>
                  <div className="font-mono text-xs text-ink-muted">
                    {line.matched_sku || t("review.choose")}
                  </div>
                </div>
                <span className="shrink-0 text-sm tabular-nums">
                  {formatQty(line.quantity)} {line.unit}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {line.source_text && (
                  <Badge tone={line.confidence >= 0.85 ? "success" : "warn"}>
                    {t("review.ai", { pct: Math.round(line.confidence * 100) })}
                  </Badge>
                )}
                {(line.confirmed || checked.has(line.line_index)) && (
                  <Badge tone="neutral">{t("review.byPerson")}</Badge>
                )}
                {avail && (
                  <Badge tone={AVAIL[avail.status].tone}>
                    {t(AVAIL[avail.status].label)}
                    {avail.status !== "unmatched" &&
                      ` · ${formatQty(avail.available)}`}
                  </Badge>
                )}
              </div>
              {line.needs_review && (
                <label className="flex gap-2.5 items-start text-sm text-ink-muted">
                  <input
                    type="checkbox"
                    disabled={busy || !line.matched_sku}
                    checked={checked.has(line.line_index)}
                    className="mt-1 accent-[var(--brand)]"
                    onChange={(e) =>
                      setChecked((prev) => {
                        const next = new Set(prev);
                        if (e.target.checked) next.add(line.line_index);
                        else next.delete(line.line_index);
                        return next;
                      })
                    }
                  />
                  {t("draft.checked")}
                </label>
              )}
            </li>
          );
        })}
      </ul>
      <div className="px-5 py-5 border-t border-line space-y-4">
        <p className="text-sm text-ink-muted">
          {missingCustomer
            ? t("review.customerRequired")
            : invalidPhone
              ? t("review.phoneRequired")
              : pending.length
                ? t("review.pending", { n: pending.length })
                : t("review.allChecked")}
        </p>
        <Button
          variant="accent"
          disabled={
            busy ||
            missingCustomer ||
            invalidPhone ||
            pending.length > 0 ||
            order.lines.length === 0
          }
          onClick={() => onApprove([], [...checked])}
        >
          {busy ? t("common.working") : t("review.approve")}
        </Button>
      </div>
    </div>
  );
}
