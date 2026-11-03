import { useState, useMemo } from "react";
import {
  Boxes,
  Warehouse,
  Database,
  Search,
  Globe,
  RotateCw,
  AlertTriangle,
  ArrowRight,
  Code2,
} from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { MockDataBanner } from "../components/ui/MockDataBanner";
import { Card, CardHeader, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { CountryBadge } from "../components/ui/CountryBadge";
import { Segmented } from "../components/ui/Segmented";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../components/ui/useToast";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { formatNumber, formatWeightKg } from "../lib/format";
import { cn } from "../lib/cn";
import { MOCK_STOCK_ITEMS, NATIVE_ERP_SAMPLES } from "../mocks/stock";
import type { NordicCountry } from "../types/api";

type CountryFilter = "all" | NordicCountry;
type SpecialFilter = "all" | "crane" | "cross_border" | "low_stock";

export default function StockPage() {
  const { t } = useI18n();
  const { pushToast } = useToast();
  useDocumentTitle(t("stock.title"));

  const [countryFilter, setCountryFilter] = useState<CountryFilter>("all");
  const [specialFilter, setSpecialFilter] = useState<SpecialFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedErpId, setSelectedErpId] = useState<"dk" | "se" | "no">("dk");

  // Filtering stock items
  const filteredStock = useMemo(() => {
    return MOCK_STOCK_ITEMS.filter((item) => {
      // Country filter
      if (countryFilter === "DK" && item.stock_dk <= 0) return false;
      if (countryFilter === "SE" && item.stock_se <= 0) return false;
      if (countryFilter === "NO" && item.stock_no <= 0) return false;

      // Special filter
      if (specialFilter === "crane" && !item.requires_crane) return false;
      if (specialFilter === "cross_border" && !item.cross_border_only) return false;
      if (specialFilter === "low_stock" && !item.is_low_stock) return false;

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesSku = item.sku.toLowerCase().includes(q);
        const matchesName = item.name.toLowerCase().includes(q);
        if (!matchesSku && !matchesName) return false;
      }

      return true;
    });
  }, [countryFilter, specialFilter, searchQuery]);

  const activeErp = useMemo(() => {
    return NATIVE_ERP_SAMPLES.find((s) => s.id === selectedErpId) || NATIVE_ERP_SAMPLES[0];
  }, [selectedErpId]);

  const handleSyncErp = () => {
    pushToast({
      title: "ERP Sync Complete",
      description: "Inventory synchronized across DK Business Central, SE Visma, and NO SAP.",
      tone: "success",
    });
  };

  const totalCatalogSkus = MOCK_STOCK_ITEMS.length;
  const crossBorderCount = MOCK_STOCK_ITEMS.filter((i) => i.cross_border_only).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("stock.title")}
        subtitle={t("stock.subtitle")}
        actions={
          <Button variant="primary" onClick={handleSyncErp}>
            <RotateCw className="w-3.5 h-3.5 mr-1.5" />
            {t("stock.syncBtn")}
          </Button>
        }
      />

      <MockDataBanner />

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("stock.kpiTotalSkus")}</p>
              <p className="text-2xl font-bold text-ink mt-1">{totalCatalogSkus}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <Boxes className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("stock.kpiWarehouses")}</p>
              <p className="text-sm font-bold text-ink mt-1.5">15 Hubs & Branches</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center">
              <Warehouse className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("stock.kpiAdapters")}</p>
              <p className="text-sm font-semibold text-ink mt-1.5">CSV · Svenska · Standard</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("stock.kpiCrossBorder")}</p>
              <p className="text-2xl font-bold text-brand mt-1">{crossBorderCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <Globe className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardBody className="p-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Segmented<CountryFilter>
              size="sm"
              value={countryFilter}
              onChange={setCountryFilter}
              options={[
                { value: "all", label: t("stock.allCountries") },
                { value: "DK", label: "DK Stock" },
                { value: "SE", label: "SE Stock" },
                { value: "NO", label: "NO Stock" },
              ]}
            />
            <Segmented<SpecialFilter>
              size="sm"
              value={specialFilter}
              onChange={setSpecialFilter}
              options={[
                { value: "all", label: t("stock.allSpecial") },
                { value: "crane", label: t("stock.craneSpecial") },
                { value: "cross_border", label: t("stock.crossBorderSpecial") },
                { value: "low_stock", label: t("stock.lowStockSpecial") },
              ]}
            />
          </div>

          <div className="relative w-72">
            <Search className="w-3.5 h-3.5 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("stock.searchPlaceholder")}
              className="w-full h-8 pl-8 pr-3 text-xs bg-surface border border-line-strong rounded-lg text-ink placeholder:text-ink-faint focus:outline-brand"
            />
          </div>
        </CardBody>
      </Card>

      {/* Unified Group Stock Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="text-sm font-bold text-ink">
              Unified Inventory ({filteredStock.length} SKUs matching)
            </h3>
            <span className="font-mono text-xs text-ink-muted">
              Auto-normalized across 3 ERPs
            </span>
          </div>
        </CardHeader>

        {filteredStock.length === 0 ? (
          <EmptyState
            icon={<Boxes className="w-6 h-6" />}
            title="No inventory records found"
            description="Try relaxing your market or handling filters."
            action={
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setCountryFilter("all");
                  setSpecialFilter("all");
                  setSearchQuery("");
                }}
              >
                Reset Filters
              </Button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-surface-2 border-b border-line text-ink-muted font-semibold">
                  <th className="py-2.5 px-4 w-36">{t("stock.colSku")}</th>
                  <th className="py-2.5 px-4 min-w-[220px]">{t("stock.colProduct")}</th>
                  <th className="py-2.5 px-3 w-16">{t("stock.colUnit")}</th>
                  <th className="py-2.5 px-3 w-24 text-right">{t("stock.colWeight")}</th>
                  <th className="py-2.5 px-3 w-28 text-center">{t("stock.colHandling")}</th>
                  <th className="py-2.5 px-3 w-24 text-right">DK Hubs</th>
                  <th className="py-2.5 px-3 w-24 text-right">SE Hubs</th>
                  <th className="py-2.5 px-3 w-24 text-right">NO Hubs</th>
                  <th className="py-2.5 px-4 w-28 text-right">{t("stock.colTotal")}</th>
                  <th className="py-2.5 px-4 w-28 text-center">{t("stock.colPrimary")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {filteredStock.map((item) => (
                  <tr key={item.sku} className="hover:bg-surface-2/40 transition-colors">
                    {/* SKU */}
                    <td className="py-3 px-4 font-mono font-bold text-ink">
                      {item.sku}
                    </td>

                    {/* Product Name */}
                    <td className="py-3 px-4">
                      <div className="font-medium text-ink">{item.name}</div>
                      {item.is_low_stock && (
                        <div className="flex items-center gap-1 text-[10px] text-danger font-semibold mt-0.5">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Low stock warning</span>
                        </div>
                      )}
                    </td>

                    {/* Unit */}
                    <td className="py-3 px-3 font-mono text-ink-muted uppercase">
                      {item.unit}
                    </td>

                    {/* Weight */}
                    <td className="py-3 px-3 text-right font-mono text-ink-muted">
                      {formatWeightKg(item.weight_kg)}
                    </td>

                    {/* Handling */}
                    <td className="py-3 px-3 text-center">
                      {item.requires_crane ? (
                        <Badge tone="warn">Crane Req</Badge>
                      ) : (
                        <Badge tone="neutral">Standard</Badge>
                      )}
                    </td>

                    {/* DK Stock */}
                    <td className="py-3 px-3 text-right font-mono">
                      <span className={cn(item.stock_dk === 0 ? "text-ink-faint" : "font-semibold text-ink")}>
                        {formatNumber(item.stock_dk)}
                      </span>
                    </td>

                    {/* SE Stock */}
                    <td className="py-3 px-3 text-right font-mono">
                      <span className={cn(item.stock_se === 0 ? "text-ink-faint" : "font-semibold text-ink")}>
                        {formatNumber(item.stock_se)}
                      </span>
                    </td>

                    {/* NO Stock */}
                    <td className="py-3 px-3 text-right font-mono">
                      <span className={cn(item.stock_no === 0 ? "text-ink-faint" : "font-semibold text-ink")}>
                        {formatNumber(item.stock_no)}
                      </span>
                    </td>

                    {/* Total Stock */}
                    <td className="py-3 px-4 text-right font-mono font-bold text-ink bg-surface-2/20">
                      {formatNumber(item.total_stock)}
                    </td>

                    {/* Primary Source */}
                    <td className="py-3 px-4 text-center">
                      {item.primary_source === "CROSS_BORDER" ? (
                        <Badge tone="brand">Cross-Border</Badge>
                      ) : (
                        <CountryBadge country={item.primary_source as NordicCountry} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Native ERP Adapter Inspector */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-brand" />
            <div>
              <h3 className="text-sm font-bold text-ink">{t("stock.inspectorTitle")}</h3>
              <p className="text-xs text-ink-muted">{t("stock.inspectorSubtitle")}</p>
            </div>
          </div>

          <Segmented<"dk" | "se" | "no">
            size="sm"
            value={selectedErpId}
            onChange={setSelectedErpId}
            options={[
              { value: "dk", label: "DK ERP (CSV)" },
              { value: "se", label: "SE ERP (JSON Svenska)" },
              { value: "no", label: "NO ERP (JSON Standard)" },
            ]}
          />
        </CardHeader>

        <CardBody className="p-5 space-y-4">
          <div className="flex items-center justify-between text-xs text-ink-muted pb-2 border-b border-line">
            <span className="font-semibold text-ink">
              Source: <strong className="text-brand font-mono">{activeErp.sourceSystem}</strong>
            </span>
            <span className="font-mono text-xs bg-surface-2 px-2 py-0.5 rounded border border-line">
              Native Format: {activeErp.format}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Raw Native ERP Payload */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold text-ink">
                <span>{t("stock.rawPayload")}</span>
                <span className="font-mono text-[10px] text-ink-faint">Raw Wire Stream</span>
              </div>
              <pre className="bg-surface-2 p-3.5 rounded-lg border border-line font-mono text-xs text-ink whitespace-pre-wrap overflow-x-auto max-h-72 select-text">
                {activeErp.rawPayload}
              </pre>
            </div>

            {/* Normalized OneOrder Output */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold text-brand-ink">
                <span className="flex items-center gap-1.5">
                  <ArrowRight className="w-3.5 h-3.5 text-brand" />
                  {t("stock.normalizedOutput")}
                </span>
                <span className="font-mono text-[10px] text-brand bg-brand-soft px-1.5 py-0.2 rounded">
                  Unified Schema
                </span>
              </div>
              <pre className="bg-surface-2 p-3.5 rounded-lg border border-brand/20 font-mono text-xs text-brand-ink whitespace-pre-wrap overflow-x-auto max-h-72 select-text">
                {activeErp.normalizedJson}
              </pre>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
