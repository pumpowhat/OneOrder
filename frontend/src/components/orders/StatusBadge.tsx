import { Badge, type BadgeTone } from "../ui/Badge.tsx";
import type { TranslationKey } from "../../i18n/en.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { RISK_LABEL, RISK_TONE, STATUS_LABEL, STATUS_TONE } from "../../lib/status.ts";
import type { CrmSyncStatus, EtaRisk, OrderStatus } from "../../types/api.ts";

export function StatusBadge({ status }: { status: OrderStatus }) {
  const { t } = useI18n();
  return <Badge tone={STATUS_TONE[status]}>{t(STATUS_LABEL[status])}</Badge>;
}

export function RiskBadge({ risk }: { risk: EtaRisk | null }) {
  const { t } = useI18n();
  if (!risk) return null;
  return <Badge tone={RISK_TONE[risk]}>{t(RISK_LABEL[risk])}</Badge>;
}

const CRM_SYNC_BADGE: Record<Exclude<CrmSyncStatus, "not_applicable">, { tone: BadgeTone; label: TranslationKey }> = {
  synced: { tone: "success", label: "crm.synced" },
  pending: { tone: "warn", label: "crm.pending" },
  failed: { tone: "danger", label: "crm.failed" },
};

export function CrmSyncBadge({ status }: { status: CrmSyncStatus }) {
  const { t } = useI18n();
  const badge = status === "not_applicable" ? null : CRM_SYNC_BADGE[status];
  return badge && <Badge tone={badge.tone}>{t(badge.label)}</Badge>;
}
