import { useI18n } from "../../i18n/useI18n.ts";
import type { TranslationKey } from "../../i18n/en.ts";
import { formatTimestamp } from "../../lib/format.ts";
import type { AuditLogEntry } from "../../types/api.ts";

const ACTION_LABEL: Record<string, TranslationKey> = {
  create_draft: "audit.create_draft",
  edit_line: "audit.edit_line",
  confirm_line: "audit.confirm_line",
  approve: "audit.approve",
  plan: "audit.plan",
  confirm: "audit.confirm",
  cancel: "audit.cancel",
};

/** Who did what and when, oldest first. Every change to an order is logged by the backend. */
export function AuditTrail({ logs }: { logs: AuditLogEntry[] }) {
  const { t } = useI18n();
  return (
    <details className="bg-surface border border-line rounded-card">
      <summary className="px-5 py-3 text-sm font-medium cursor-pointer">
        {t("audit.title")} <span className="text-ink-muted font-normal">({logs.length})</span>
      </summary>
      <ol className="px-5 pb-4 space-y-2 border-t border-line pt-3">
        {logs.map((log) => (
          <li key={log.id} className="flex items-baseline gap-3 text-sm">
            <span className="w-36 shrink-0 text-xs text-ink-muted tabular-nums">{formatTimestamp(log.timestamp)}</span>
            <span className="flex-1">{ACTION_LABEL[log.action] ? t(ACTION_LABEL[log.action]) : log.action}</span>
            <span className="text-xs text-ink-muted">{log.user}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}
