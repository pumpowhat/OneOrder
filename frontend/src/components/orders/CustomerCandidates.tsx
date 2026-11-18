import { useEffect, useState } from "react";
import { getCustomerCandidates } from "../../api/orders.ts";
import { useApi } from "../../hooks/useApi.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import type { CrmCustomerLink, CustomerCandidate, CustomerLookup } from "../../types/api.ts";
import { Badge } from "../ui/Badge.tsx";
import { Button } from "../ui/Button.tsx";

export function CustomerCandidates({
  orderId,
  link,
  lookup,
  disabled,
  onSelect,
  onManual,
}: {
  orderId: string;
  link?: CrmCustomerLink;
  lookup?: CustomerLookup;
  disabled: boolean;
  onSelect: (candidate: CustomerCandidate) => void;
  onManual: () => void;
}) {
  const { t } = useI18n();
  const name = lookup?.name.trim();
  const phone = lookup?.phone.trim();
  const [settled, setSettled] = useState<CustomerLookup | undefined>(
    name === undefined || phone === undefined ? undefined : { name, phone },
  );
  useEffect(() => {
    if (name === undefined || phone === undefined) return;
    const timer = window.setTimeout(() => setSettled({ name, phone }), 300);
    return () => window.clearTimeout(timer);
  }, [name, phone]);
  const { data, error, loading, reload } = useApi(
    (signal) => getCustomerCandidates(orderId, signal, settled),
    [orderId, settled?.name, settled?.phone],
  );

  const refreshing = loading || name !== settled?.name || phone !== settled?.phone;
  // Older backends have no candidates endpoint.
  if (error?.status === 404 || data?.crm === "none" || (!data && !error)) return null;
  const candidates = error ? [] : (data?.candidates ?? []);
  const lookupFailed = !!(error || data?.error);

  return (
    <section aria-label={t("crm.candidates")} className="space-y-2 rounded-lg border border-line bg-surface-2 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{t("crm.candidates")}</h3>
        <div className="flex flex-wrap items-center gap-2">
          {!link?.crm_account_id && <span className="text-xs text-ink-muted">{t("crm.notLinked")}</span>}
          <Badge tone="info">{t("crm.salesforce")}</Badge>
        </div>
      </div>
      {refreshing && <p role="status" className="text-sm text-ink-muted">{t("common.loading")}</p>}
      {!refreshing && lookupFailed && (
        <div role="status" className="flex flex-wrap items-center gap-2 text-sm text-warn">
          <span>{t("crm.lookupError")}</span>
          <Button size="sm" disabled={disabled} onClick={reload}>{t("common.retry")}</Button>
        </div>
      )}
      {!refreshing && !lookupFailed && candidates.length === 0 && (
        <p role="status" className="text-sm text-ink-muted">{t("crm.customerNotFound")}</p>
      )}
      {!refreshing && candidates.length > 0 && data?.ambiguous && (
        <p role="status" className="text-sm text-warn">{t("crm.ambiguous")}</p>
      )}
      {!refreshing && candidates.length > 0 && (
        <ul className="space-y-2">
          {candidates.map((candidate) => {
            const selected = candidate.crm_account_id === link?.crm_account_id
              && candidate.crm_contact_id === link?.crm_contact_id;
            return (
              <li key={`${candidate.crm_account_id}-${candidate.crm_contact_id ?? ""}`}>
                <button
                  type="button"
                  disabled={disabled || selected}
                  className="flex w-full flex-wrap items-center justify-between gap-2 rounded-md border border-line bg-surface px-3 py-2 text-start hover:border-accent disabled:cursor-default"
                  onClick={() => onSelect(candidate)}
                >
                  <span>
                    <span className="block text-sm font-medium">{candidate.name}</span>
                    <span className="block text-xs text-ink-muted">
                      {[candidate.phone, candidate.city, candidate.country].filter(Boolean).join(" · ")}
                    </span>
                  </span>
                  {selected && <Badge tone="success">{t("crm.selected")}</Badge>}
                </button>
              </li>
            );
          })}
        </ul>
      )}
      <Button size="sm" variant="ghost" disabled={disabled} onClick={onManual}>
        {t("crm.useTypedName")}
      </Button>
    </section>
  );
}
