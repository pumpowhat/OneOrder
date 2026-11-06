import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import { getStock } from "../api/stock.ts";
import { useApi } from "../hooks/useApi.ts";
import { useDocumentTitle } from "../hooks/useDocumentTitle.ts";
import { useI18n } from "../i18n/useI18n.ts";
import { errorMessage } from "../lib/errors.ts";
import { formatQty } from "../lib/format.ts";
import type { NordicCountry, StockItem, StockLevel } from "../types/api.ts";
import { Badge, type BadgeTone } from "../components/ui/Badge.tsx";
import { Card, CardBody } from "../components/ui/Card.tsx";
import { CountryBadge } from "../components/ui/CountryBadge.tsx";
import { EmptyState } from "../components/ui/EmptyState.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";
import { Segmented } from "../components/ui/Segmented.tsx";
import { cn } from "../lib/cn.ts";

const COUNTRIES: NordicCountry[] = ["DK", "SE", "NO"];
const PAGE_SIZE = 50;
const LEVEL_TONE: Record<StockLevel, BadgeTone> = { ok: "success", low: "warn", out: "danger" };

type CountryFilter = NordicCountry | "all";

export default function StockPage() {
  const { t } = useI18n();
  useDocumentTitle(t("nav.stock"));
  const [country, setCountry] = useState<CountryFilter>("all");
  const [query, setQuery] = useState("");
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [shown, setShown] = useState(PAGE_SIZE);

  const { data, error, loading, reload } = useApi(
    (signal) => getStock({ country: country === "all" ? undefined : country, q: query, onlyIssues }, signal),
    [country, query, onlyIssues],
  );
  const items = data?.items ?? [];
  const visible = items.slice(0, shown);

  const levelLabel = (item: StockItem) =>
    item.level === "ok" ? t("stock.levelOk") : item.level === "low" ? t("stock.levelLow") : t("stock.levelOut");

  return (
    <div className="space-y-6">
      <PageHeader title={t("nav.stock")} subtitle={t("stock.subtitle")} />

      <div className="grid grid-cols-3 gap-4">
        {COUNTRIES.map((c) => (
          <Card key={c}>
            <CardBody className="space-y-1">
              <CountryBadge country={c} />
              <div className="text-2xl font-semibold tabular-nums">{data ? data.summary[c].skus : "…"}</div>
              <div className="text-xs text-ink-muted">
                {t("stock.skuCount")}
                {data && data.summary[c].out_or_low > 0 && (
                  <span className="text-warn"> · {t("stock.issues", { n: data.summary[c].out_or_low })}</span>
                )}
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-4 h-4 text-ink-faint absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShown(PAGE_SIZE);
            }}
            placeholder={t("stock.search")}
            aria-label={t("stock.search")}
            className="w-full h-9 pl-9 pr-3 rounded-lg border border-line-strong bg-surface text-sm"
          />
        </label>
        <Segmented<CountryFilter>
          options={[{ value: "all", label: t("common.all") }, ...COUNTRIES.map((c) => ({ value: c, label: c }))]}
          value={country}
          onChange={(value) => {
            setCountry(value);
            setShown(PAGE_SIZE);
          }}
        />
        <label className="inline-flex items-center gap-2 text-sm text-ink-muted cursor-pointer">
          <input type="checkbox" checked={onlyIssues} onChange={(e) => {
              setOnlyIssues(e.target.checked);
              setShown(PAGE_SIZE);
            }} className="w-4 h-4 accent-[var(--brand)]" />
          {t("stock.onlyIssues")}
        </label>
      </div>

      {error ? (
        <Card>
          <CardBody className="flex items-center justify-between gap-4">
            <span className="text-sm text-danger">{errorMessage(error, t)}</span>
            <button type="button" onClick={reload} className="text-sm font-medium text-brand hover:underline">
              {t("common.retry")}
            </button>
          </CardBody>
        </Card>
      ) : !data && loading ? (
        <p className="text-sm text-ink-muted">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <EmptyState title={t("stock.emptyTitle")} description={t("stock.emptyText")} />
      ) : (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-ink-muted border-b border-line bg-surface-2">
                <th className="px-5 py-2.5 font-medium">{t("stock.item")}</th>
                {COUNTRIES.map((c) => (
                  <th key={c} className="px-3 py-2.5 font-medium text-right">{c}</th>
                ))}
                <th className="px-3 py-2.5 font-medium text-right">{t("stock.total")}</th>
                <th className="px-5 py-2.5 font-medium">{t("common.status")}</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((item) => {
                const expanded = open === item.sku;
                return (
                  <Fragment key={item.sku}>
                    <tr className="border-b border-line hover:bg-surface-2">
                      <td className="px-5 py-2.5">
                        <button
                          type="button"
                          onClick={() => setOpen(expanded ? null : item.sku)}
                          aria-expanded={expanded}
                          className="flex items-center gap-2 text-left cursor-pointer"
                        >
                          {expanded ? <ChevronDown className="w-4 h-4 text-ink-faint" /> : <ChevronRight className="w-4 h-4 text-ink-faint" />}
                          <span>
                            <span className="block font-medium">{item.name}</span>
                            <span className="block text-xs text-ink-muted font-mono">{item.sku}</span>
                          </span>
                        </button>
                      </td>
                      {COUNTRIES.map((c) => (
                        <td key={c} className={cn("px-3 py-2.5 text-right tabular-nums", item.by_country[c].available <= 0 && "text-ink-faint")}>
                          {formatQty(item.by_country[c].available)}
                        </td>
                      ))}
                      <td className="px-3 py-2.5 text-right tabular-nums font-medium">
                        {formatQty(item.total_available)} <span className="text-xs text-ink-muted font-normal">{item.unit}</span>
                      </td>
                      <td className="px-5 py-2.5">
                        <span className="inline-flex items-center gap-1.5">
                          <Badge tone={LEVEL_TONE[item.level]}>{levelLabel(item)}</Badge>
                          {item.single_country && <Badge tone="info">{t("stock.singleCountry")}</Badge>}
                        </span>
                      </td>
                    </tr>
                    {expanded && (
                      <tr className="border-b border-line bg-surface-2">
                        <td colSpan={6} className="px-5 py-3">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="text-ink-muted text-left">
                                <th className="py-1 font-medium">{t("stock.warehouse")}</th>
                                <th className="py-1 font-medium text-right">{t("stock.onHand")}</th>
                                <th className="py-1 font-medium text-right">{t("stock.reserved")}</th>
                                <th className="py-1 font-medium text-right">{t("stock.available")}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {item.warehouses.map((w) => (
                                <tr key={w.code} className="border-t border-line">
                                  <td className="py-1.5">
                                    <span className="inline-flex items-center gap-2">
                                      <CountryBadge country={w.country} />
                                      <span>{w.name}</span>
                                      <span className="text-ink-faint font-mono">{w.code}</span>
                                    </span>
                                  </td>
                                  <td className="py-1.5 text-right tabular-nums">{formatQty(w.on_hand)}</td>
                                  <td className="py-1.5 text-right tabular-nums">{formatQty(w.reserved)}</td>
                                  <td className="py-1.5 text-right tabular-nums font-medium">{formatQty(w.available)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
          {items.length > shown && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-line bg-surface-2 text-sm text-ink-muted">
              <span>{t("stock.showing", { shown: visible.length, total: items.length })}</span>
              <button type="button" onClick={() => setShown((n) => n + PAGE_SIZE)} className="font-medium text-brand hover:underline cursor-pointer">
                {t("stock.showMore")}
              </button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
