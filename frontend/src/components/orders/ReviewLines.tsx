import { useMemo, useState } from "react";
import { Button } from "../ui/Button.tsx";
import { Badge, type BadgeTone } from "../ui/Badge.tsx";
import { useI18n } from "../../i18n/useI18n.ts";
import type { TranslationKey } from "../../i18n/en.ts";
import { formatQty } from "../../lib/format.ts";
import { cn } from "../../lib/cn.ts";
import type { AvailabilityStatus, LineAvailability, LineCorrection, Order, OrderLine } from "../../types/api.ts";

const AVAIL: Record<AvailabilityStatus, { tone: BadgeTone; label: TranslationKey }> = {
  ok: { tone: "success", label: "avail.ok" },
  partial: { tone: "warn", label: "avail.partial" },
  none: { tone: "danger", label: "avail.none" },
  unmatched: { tone: "neutral", label: "avail.unmatched" },
};

const REVIEW_THRESHOLD = 0.85;

interface Edit {
  sku?: string;
  quantity?: number;
}

interface Props {
  order: Order;
  availability: LineAvailability[];
  busy: boolean;
  onApprove: (corrections: LineCorrection[], confirmLines: number[]) => void;
}

/** The extracted lines with confidence and stock pre-check; the clerk fixes and ticks the doubtful ones. */
export function ReviewLines({ order, availability, busy, onApprove }: Props) {
  const { t } = useI18n();
  const [edits, setEdits] = useState<Record<number, Edit>>({});
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const stock = useMemo(() => new Map(availability.map((a) => [a.line_index, a])), [availability]);

  const sku = (line: OrderLine) => edits[line.line_index]?.sku ?? line.matched_sku ?? "";
  const pending = order.lines.filter((l) => (l.needs_review && !checked.has(l.line_index)) || !sku(l));

  const edit = (line: OrderLine, patch: Edit) => {
    setEdits((prev) => ({ ...prev, [line.line_index]: { ...prev[line.line_index], ...patch } }));
    setChecked((prev) => new Set(prev).add(line.line_index));
  };

  const approve = () => {
    const corrections: LineCorrection[] = [];
    for (const [index, e] of Object.entries(edits)) {
      corrections.push({ line_index: Number(index), sku: e.sku, quantity: e.quantity, confirmed: true });
    }
    const confirmLines = [...checked].filter((i) => !(i in edits));
    onApprove(corrections, confirmLines);
  };

  return (
    <div>
      <ul className="divide-y divide-line">
        {order.lines.map((line) => {
          const flagged = line.needs_review || !sku(line);
          const done = checked.has(line.line_index);
          const avail = stock.get(line.line_index);
          const quantity = edits[line.line_index]?.quantity ?? line.quantity;
          const options = line.candidates.some((c) => c.sku === sku(line))
            ? line.candidates
            : [...(sku(line) ? [{ sku: sku(line), name: sku(line), score: line.match_score ?? 0 }] : []), ...line.candidates];

          return (
            <li key={line.line_index} className={cn("px-5 py-4 space-y-2.5", flagged && !done && "bg-warn-soft/40")}>
              <div className="flex items-start gap-3">
                {flagged ? (
                  <input
                    type="checkbox"
                    checked={done}
                    onChange={(e) =>
                      setChecked((prev) => {
                        const next = new Set(prev);
                        if (e.target.checked) next.add(line.line_index);
                        else next.delete(line.line_index);
                        return next;
                      })
                    }
                    aria-label={t("review.checkLine", { n: line.line_index + 1 })}
                    className="mt-1 w-4 h-4 accent-[var(--brand)]"
                  />
                ) : (
                  <span className="mt-1 w-4 h-4" aria-hidden="true" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium break-words">{line.description}</div>
                  {line.source_text && line.source_text !== line.description && (
                    <div className="text-xs text-ink-muted break-words">“{line.source_text}”</div>
                  )}
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <input
                    type="number"
                    min={0}
                    step="any"
                    value={quantity}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      if (value > 0) edit(line, { quantity: value });
                    }}
                    aria-label={t("review.quantity")}
                    className="w-20 h-8 px-2 rounded-md border border-line-strong bg-surface text-sm text-right tabular-nums"
                  />
                  <span className="text-xs text-ink-muted w-8">{line.unit}</span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pl-7">
                {flagged ? (
                  options.length > 0 ? (
                    <select
                      value={sku(line)}
                      onChange={(e) => edit(line, { sku: e.target.value })}
                      aria-label={t("review.product")}
                      className="h-8 w-full max-w-[420px] min-w-0 px-2 rounded-md border border-line-strong bg-surface text-sm"
                    >
                      {!sku(line) && <option value="">{t("review.choose")}</option>}
                      {options.map((c) => (
                        <option key={c.sku} value={c.sku}>
                          {c.name} · {c.sku}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={sku(line)}
                      placeholder={t("review.typeSku")}
                      onChange={(e) => setEdits((p) => ({ ...p, [line.line_index]: { ...p[line.line_index], sku: e.target.value.trim() } }))}
                      aria-label={t("review.product")}
                      className="h-8 w-48 px-2 rounded-md border border-line-strong bg-surface text-sm font-mono"
                    />
                  )
                ) : (
                  <span className="text-xs font-mono text-info">{sku(line)}</span>
                )}
                <Badge tone={line.confidence >= REVIEW_THRESHOLD ? "success" : "warn"}>
                  {t("review.ai", { pct: Math.round(line.confidence * 100) })}
                  {line.confidence < REVIEW_THRESHOLD && ` · ${t("review.check")}`}
                </Badge>
                {avail && (
                  <Badge tone={AVAIL[avail.status].tone}>
                    {t(AVAIL[avail.status].label)}
                    {avail.status !== "unmatched" && ` · ${formatQty(avail.available)}`}
                  </Badge>
                )}
                {(done || line.confirmed) && <Badge tone="neutral">{t("review.byPerson")}</Badge>}
              </div>
            </li>
          );
        })}
      </ul>

      <div className="flex items-center justify-between gap-4 px-5 py-4 border-t border-line bg-surface-2 rounded-b-card">
        <span className="text-sm text-ink-muted">
          {pending.length > 0 ? t("review.pending", { n: pending.length }) : t("review.allChecked")}
        </span>
        <Button variant="accent" disabled={busy || pending.length > 0} onClick={approve}>
          {busy ? t("common.working") : t("review.approve")}
        </Button>
      </div>
    </div>
  );
}
