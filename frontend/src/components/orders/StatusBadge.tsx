import { Badge } from "../ui/Badge.tsx";
import { useI18n } from "../../i18n/useI18n.ts";
import { RISK_LABEL, RISK_TONE, STATUS_LABEL, STATUS_TONE } from "../../lib/status.ts";
import type { EtaRisk, OrderStatus } from "../../types/api.ts";

export function StatusBadge({ status }: { status: OrderStatus }) {
  const { t } = useI18n();
  return <Badge tone={STATUS_TONE[status]}>{t(STATUS_LABEL[status])}</Badge>;
}

export function RiskBadge({ risk }: { risk: EtaRisk | null }) {
  const { t } = useI18n();
  if (!risk) return null;
  return <Badge tone={RISK_TONE[risk]}>{t(RISK_LABEL[risk])}</Badge>;
}
