import { useState } from "react";
import { useApi } from "../../hooks/useApi.ts";
import { listCatalog } from "../../api/orders.ts";
import type { DraftOrderInput, Order } from "../../types/api.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { errorMessage } from "../../lib/errors.ts";
import { Button } from "../ui/Button.tsx";
import { PhoneInput } from "../ui/PhoneInput.tsx";

const input =
  "w-full min-w-0 h-10 rounded-md border border-line-strong bg-surface px-3 text-sm text-ink focus-visible:outline-2 focus-visible:outline-[var(--brand)]";
type Row = {
  key: string;
  line_index?: number;
  sku: string;
  description: string;
  quantity: string;
  confirmed: boolean;
};

export function OrderDraftForm({
  order,
  onSave,
  onCancel,
}: {
  order?: Order;
  onSave: (payload: DraftOrderInput) => Promise<unknown>;
  onCancel?: () => void;
}) {
  const { t } = useI18n();
  const catalog = useApi((signal) => listCatalog(signal), []);
  const [customer, setCustomer] = useState(order?.customer ?? "");
  const [phone, setPhone] = useState(order?.customer_phone ?? "");
  const [site, setSite] = useState(order?.delivery_site ?? "");
  const [date, setDate] = useState(order?.requested_date ?? "");
  const [rows, setRows] = useState<Row[]>(
    () =>
      order?.lines.map((l) => ({
        key: String(l.line_index),
        line_index: l.line_index,
        sku: l.matched_sku ?? "",
        description: l.description,
        quantity: String(l.quantity),
        confirmed: l.confirmed,
      })) ?? [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const patch = (key: string, values: Partial<Row>) =>
    setRows((prev) =>
      prev.map((r) => (r.key === key ? { ...r, ...values } : r)),
    );
  return (
    <form
      className="p-5 md:p-6 space-y-8"
      onSubmit={async (event) => {
        event.preventDefault();
        setBusy(true);
        setError(null);
        try {
          await onSave({
            customer: customer.trim() || null,
            customer_phone: phone.trim() || null,
            delivery_site: site.trim() || null,
            requested_date: date || null,
            lines: rows.map((r) => ({
              line_index: r.line_index,
              sku: r.sku || null,
              description: r.description.trim(),
              quantity: Number(r.quantity),
              confirmed: r.confirmed,
            })),
          });
        } catch (err) {
          setError(err);
        } finally {
          setBusy(false);
        }
      }}
    >
      <fieldset disabled={busy} className="space-y-8 min-w-0">
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-sm">
              {t("draft.customerSection")}
            </h3>
            <p className="mt-1 text-xs text-ink-muted">{t("draft.hint")}</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-5">
            <label className="block space-y-2 text-sm">
              <span>{t("common.customer")}</span>
              <input
                className={input}
                value={customer}
                maxLength={255}
                onChange={(e) => setCustomer(e.target.value)}
              />
            </label>
            <div className="space-y-2 text-sm">
              <label htmlFor="draft-phone">{t("common.customerPhone")}</label>
              <PhoneInput
                required={false}
                id="draft-phone"
                value={phone}
                onChange={setPhone}
                disabled={busy}
              />
            </div>
            <label className="block space-y-2 text-sm">
              <span>{t("common.site")}</span>
              <input
                className={input}
                value={site}
                maxLength={255}
                onChange={(e) => setSite(e.target.value)}
              />
            </label>
            <label className="block space-y-2 text-sm">
              <span>{t("common.requestedDate")}</span>
              <input
                type="date"
                className={input}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </label>
          </div>
        </div>
        <div className="space-y-4 border-t border-line pt-6">
          <h3 className="font-semibold text-sm">{t("draft.lines")}</h3>
          {catalog.error && (
            <div role="alert" className="text-sm text-danger space-y-2">
              <p>{errorMessage(catalog.error, t)}</p>
              <Button onClick={catalog.reload}>{t("common.retry")}</Button>
            </div>
          )}
          {catalog.loading && (
            <p className="text-sm text-ink-muted">{t("common.loading")}</p>
          )}
          {rows.length === 0 && (
            <p className="rounded-md bg-surface-2 p-5 text-sm text-ink-muted">
              {t("draft.empty")}
            </p>
          )}
          {rows.map((row, index) => (
            <div
              key={row.key}
              className="rounded-card border border-line p-4 space-y-4"
            >
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs font-medium text-ink-muted">
                  {t("draft.line", { n: index + 1 })}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    setRows((prev) => prev.filter((r) => r.key !== row.key))
                  }
                >
                  {t("draft.remove")}
                </Button>
              </div>
              <label className="block space-y-2 text-sm">
                <span>{t("review.product")}</span>
                <select
                  className={input}
                  value={row.sku}
                  disabled={catalog.loading || !!catalog.error}
                  onChange={(e) => {
                    const product = catalog.data?.find(
                      (p) => p.sku === e.target.value,
                    );
                    patch(row.key, {
                      sku: e.target.value,
                      ...(product ? { description: product.name } : {}),
                      confirmed: false,
                    });
                  }}
                >
                  <option value="">{t("review.choose")}</option>
                  {row.sku && !catalog.data?.some((p) => p.sku === row.sku) && (
                    <option value={row.sku}>{row.sku}</option>
                  )}
                  {catalog.data?.map((p) => (
                    <option key={p.sku} value={p.sku}>
                      {p.name} · {p.sku}
                    </option>
                  ))}
                </select>
              </label>
              <div className="grid sm:grid-cols-[1fr_140px] gap-4">
                <label className="block space-y-2 text-sm">
                  <span>{t("draft.description")}</span>
                  <input
                    required
                    maxLength={255}
                    className={input}
                    value={row.description}
                    onChange={(e) =>
                      patch(row.key, {
                        description: e.target.value,
                        confirmed: false,
                      })
                    }
                  />
                </label>
                <label className="block space-y-2 text-sm">
                  <span>
                    {t("review.quantity")}{" "}
                    {catalog.data?.find((p) => p.sku === row.sku)?.unit &&
                      `(${catalog.data.find((p) => p.sku === row.sku)?.unit})`}
                  </span>
                  <input
                    required
                    type="number"
                    min="0.000000001"
                    step="any"
                    className={input}
                    value={row.quantity}
                    onChange={(e) =>
                      patch(row.key, {
                        quantity: e.target.value,
                        confirmed: false,
                      })
                    }
                  />
                </label>
              </div>
              <label className="flex items-start gap-2.5 text-sm text-ink-muted">
                <input
                  type="checkbox"
                  className="mt-1 accent-[var(--brand)]"
                  checked={row.confirmed}
                  onChange={(e) =>
                    patch(row.key, { confirmed: e.target.checked })
                  }
                />
                {t("draft.checked")}
              </label>
            </div>
          ))}
          <Button
            disabled={rows.length >= 500}
            onClick={() =>
              setRows((prev) => [
                ...prev,
                {
                  key: crypto.randomUUID(),
                  sku: "",
                  description: "",
                  quantity: "1",
                  confirmed: false,
                },
              ])
            }
          >
            {t("draft.add")}
          </Button>
        </div>
      </fieldset>
      {!!error && (
        <p role="alert" className="text-sm text-danger">
          {errorMessage(error, t)}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-5">
        <Button
          variant="accent"
          type="submit"
          disabled={busy || catalog.loading || !!catalog.error}
        >
          {busy ? t("common.working") : t("draft.save")}
        </Button>
        {onCancel && (
          <Button disabled={busy} variant="ghost" onClick={onCancel}>
            {t("draft.cancel")}
          </Button>
        )}
      </div>
    </form>
  );
}
