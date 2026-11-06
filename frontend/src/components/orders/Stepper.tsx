import { Check } from "lucide-react";
import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";
import type { OrderStatus } from "../../types/api.ts";

const STEP_OF: Record<OrderStatus, number> = { draft: 0, approved: 1, planned: 2, confirmed: 3, cancelled: -1 };

/** Review → Plan → Confirm: where the order is in the two-approval flow. */
export function Stepper({ status }: { status: OrderStatus }) {
  const { t } = useI18n();
  const current = STEP_OF[status];
  const steps = [t("step.review"), t("step.plan"), t("step.confirm")];

  return (
    <ol className="flex items-center gap-2" aria-label={t("step.label")}>
      {steps.map((label, i) => {
        const done = current > i;
        const active = current === i;
        return (
          <li key={label} className="flex items-center gap-2" aria-current={active ? "step" : undefined}>
            <span
              className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold border",
                done && "bg-success text-on-brand border-success",
                active && "bg-brand text-on-brand border-brand",
                !done && !active && "bg-surface text-ink-faint border-line-strong",
              )}
            >
              {done ? <Check className="w-3.5 h-3.5" aria-hidden="true" /> : i + 1}
            </span>
            <span className={cn("text-sm", active ? "font-semibold text-ink" : "text-ink-muted")}>{label}</span>
            {i < steps.length - 1 && <span className="w-8 h-px bg-line-strong mx-1" aria-hidden="true" />}
          </li>
        );
      })}
    </ol>
  );
}
