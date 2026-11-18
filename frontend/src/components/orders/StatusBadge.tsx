import { Badge, type BadgeTone } from "../ui/Badge.tsx";
import type { TranslationKey } from "../../i18n/en.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { RISK_LABEL, RISK_TONE, STATUS_LABEL, STATUS_TONE } from "../../lib/status.ts";
import type { CrmSync, CrmSyncStatus, EtaRisk, OrderStatus } from "../../types/api.ts";

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

export function CrmSyncBadge({ status, reason }: { status: CrmSyncStatus; reason?: CrmSync["reason"] }) {
  const { t } = useI18n();
  if (status === "not_applicable") {
    return (
      <Badge tone="neutral">
        {t(reason === "crm_disabled" ? "crm.disabledCountry" : "crm.customerUnlinked")}
      </Badge>
    );
  }
  const badge = CRM_SYNC_BADGE[status];
  return <Badge tone={badge.tone}>{t(badge.label)}</Badge>;
}
