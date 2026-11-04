import { useState, useMemo } from "react";
import { useNavigate } from "react-router";
import {
  Camera,
  Mail,
  FileSpreadsheet,
  AlertTriangle,
  ArrowRight,
  Search,
  Sparkles,
  Layers,
  Inbox as InboxIcon,
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
import { formatIsoDate } from "../lib/format";
import { cn } from "../lib/cn";
import { MOCK_INBOX_ITEMS } from "../mocks/inbox";
import type { InboxItem, SourceType, NordicCountry, OrderStatus } from "../types/api";
import type { TranslationKey } from "../i18n/en";

type SourceFilter = "all" | SourceType;
type CountryFilter = "all" | NordicCountry;

const SOURCE_ICONS: Record<SourceType, typeof Camera> = {
  image: Camera,
  email: Mail,
  excel: FileSpreadsheet,
};

const STATUS_TONES: Record<OrderStatus, "neutral" | "brand" | "success" | "warn" | "danger" | "info"> = {
  draft: "warn",
  approved: "info",
  planned: "brand",
  confirmed: "success",
};

const STATUS_KEYS: Record<OrderStatus, TranslationKey> = {
  draft: "common.draft",
  approved: "common.approved",
  planned: "common.planned",
  confirmed: "common.confirmedStatus",
};

export default function InboxPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { pushToast } = useToast();
  useDocumentTitle(t("inbox.title"));

  const [items] = useState<InboxItem[]>(MOCK_INBOX_ITEMS);
  const [selectedId, setSelectedId] = useState<string>(MOCK_INBOX_ITEMS[0]?.id || "");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [countryFilter, setCountryFilter] = useState<CountryFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Filtered items
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (sourceFilter !== "all" && item.sourceType !== sourceFilter) return false;
      if (countryFilter !== "all" && item.country !== countryFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesCustomer = item.customer.toLowerCase().includes(q);
        const matchesSite = item.deliverySite.toLowerCase().includes(q);
        const matchesFile = item.sourceName.toLowerCase().includes(q);
        if (!matchesCustomer && !matchesSite && !matchesFile) return false;
      }
      return true;
    });
  }, [items, sourceFilter, countryFilter, searchQuery]);

  // Ensure an item is always selected if available
  const selectedItem = useMemo(() => {
    return (
      filteredItems.find((i) => i.id === selectedId) ||
      filteredItems[0] ||
      null
    );
  }, [filteredItems, selectedId]);

  const handleSimulateIntake = () => {
    pushToast({
      title: t("inbox.simulatedToast"),
      description: "NCC Danmark A/S (Aarhus Havn) flagged for human verification.",
      tone: "warn",
    });
    if (items.length > 0) {
      setSelectedId(items[0].id);
    }
  };

  const totalCount = items.length;
  const reviewCount = items.filter((i) => i.flaggedCount > 0).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("inbox.title")}
        subtitle={t("inbox.subtitle")}
        actions={
          <Button variant="primary" onClick={handleSimulateIntake}>
            <Sparkles className="w-4 h-4 mr-1.5" />
            {t("inbox.simulateIntake")}
          </Button>
        }
      />

      <MockDataBanner />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("inbox.totalRequests")}</p>
              <p className="text-2xl font-bold text-ink mt-1">{totalCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("inbox.needsReviewCard")}</p>
              <p className="text-2xl font-bold text-warn mt-1">{reviewCount}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-warn-soft text-warn flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("inbox.channels")}</p>
              <p className="text-sm font-semibold text-ink mt-1.5 truncate">
                Photo · Email · Excel
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center">
              <Camera className="w-5 h-5" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-ink-muted font-medium">{t("inbox.markets")}</p>
              <p className="text-sm font-semibold text-ink mt-1.5 font-mono">
                DK · SE · NO
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-surface-2 text-ink-muted flex items-center justify-center font-bold text-xs font-mono">
              3 DC
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardBody className="p-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Segmented<SourceFilter>
              size="sm"
              value={sourceFilter}
              onChange={setSourceFilter}
              options={[
                { value: "all", label: t("common.all") },
                { value: "image", label: t("inbox.sourcePhoto") },
                { value: "email", label: t("inbox.sourceEmail") },
                { value: "excel", label: t("inbox.sourceExcel") },
              ]}
            />
            <Segmented<CountryFilter>
              size="sm"
              value={countryFilter}
              onChange={setCountryFilter}
              options={[
                { value: "all", label: t("common.all") },
                { value: "DK", label: "DK" },
                { value: "SE", label: "SE" },
                { value: "NO", label: "NO" },
              ]}
            />
          </div>

          <div className="relative w-72">
            <Search className="w-3.5 h-3.5 text-ink-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("inbox.searchPlaceholder")}
              className="w-full h-8 pl-8 pr-3 text-xs bg-surface border border-line-strong rounded-lg text-ink placeholder:text-ink-faint focus:outline-brand"
            />
          </div>
        </CardBody>
      </Card>

      {/* Master-Detail Split View */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* Left Column: Intake Queue */}
        <div className="col-span-5 space-y-3">
          {filteredItems.length === 0 ? (
            <EmptyState
              icon={<InboxIcon className="w-6 h-6" />}
              title={t("inbox.emptyTitle")}
              description={t("inbox.emptyDesc")}
              action={
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setSourceFilter("all");
                    setCountryFilter("all");
                    setSearchQuery("");
                  }}
                >
                  {t("common.reset")}
                </Button>
              }
            />
          ) : (
            filteredItems.map((item) => {
              const isSelected = selectedItem?.id === item.id;
              const SourceIcon = SOURCE_ICONS[item.sourceType] || Camera;
              const statusLabel = t(STATUS_KEYS[item.status]);

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  className={cn(
                    "p-4 rounded-card border transition-all cursor-pointer bg-surface",
                    isSelected
                      ? "border-brand ring-1 ring-brand shadow-sm bg-brand-soft/20"
                      : "border-line hover:border-line-strong hover:bg-surface-2/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-surface-2 border border-line flex items-center justify-center text-ink-muted shrink-0">
                        <SourceIcon className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <h3 className="text-xs font-bold text-ink leading-tight truncate max-w-[190px]">
                          {item.customer}
                        </h3>
                        <p className="text-[11px] text-ink-muted truncate max-w-[190px]">
                          {item.deliverySite}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <CountryBadge country={item.country} />
                      <Badge tone={STATUS_TONES[item.status]}>{statusLabel}</Badge>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-line/60 flex items-center justify-between text-[11px] text-ink-muted">
                    <span className="font-mono text-ink-faint truncate max-w-[140px]">
                      {item.sourceName}
                    </span>
                    <div className="flex items-center gap-2">
                      <span>{item.lineCount} {t("common.lines")}</span>
                      {item.flaggedCount > 0 && (
                        <Badge tone="warn" className="px-1.5 py-0 text-[10px]">
                          <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />
                          {item.flaggedCount} {t("inbox.flaggedLines")}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Detail Panel */}
        <div className="col-span-7">
          {selectedItem ? (
            <Card>
              <CardHeader className="flex items-start justify-between gap-4 py-4">
                <div>
                  <div className="flex items-center gap-2">
                    <CountryBadge country={selectedItem.country} />
                    <h2 className="text-base font-bold text-ink">{selectedItem.customer}</h2>
                    <Badge tone={STATUS_TONES[selectedItem.status]}>
                      {t(STATUS_KEYS[selectedItem.status])}
                    </Badge>
                  </div>
                  <p className="text-xs text-ink-muted mt-1">{selectedItem.deliverySite}</p>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-[11px] text-ink-faint uppercase font-semibold">
                    {t("common.requestedDate")}
                  </p>
                  <p className="text-xs font-mono font-medium text-ink mt-0.5">
                    {formatIsoDate(selectedItem.requestedDate)}
                  </p>
                </div>
              </CardHeader>

              <CardBody className="p-5 space-y-5">
                {/* AI Extraction Overview Bar */}
                <div className="p-3.5 rounded-lg bg-surface-2 border border-line flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-brand-soft text-brand flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-ink">
                        {t("inbox.extractionSummary")}
                      </p>
                      <p className="text-[11px] text-ink-muted">
                        {selectedItem.lineCount} {t("inbox.cleanLines")} ·{" "}
                        {selectedItem.flaggedCount > 0 ? (
                          <span className="text-warn font-medium">
                            {selectedItem.flaggedCount} {t("inbox.flaggedLines")}
                          </span>
                        ) : (
                          <span className="text-success font-medium">
                            {t("review.allConfirmed")}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate(`/review?orderId=${selectedItem.orderId}`)}
                  >
                    <span>{t("inbox.reviewCta")}</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </div>

                {/* Raw Contractor Input Box */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-ink">
                      {selectedItem.rawPreviewTitle}
                    </p>
                    <span className="font-mono text-[11px] text-ink-muted">
                      {selectedItem.sourceName}
                    </span>
                  </div>
                  <div className="bg-surface-2 p-4 rounded-lg border border-line font-mono text-xs text-ink leading-relaxed whitespace-pre-wrap select-text max-h-[360px] overflow-y-auto">
                    {selectedItem.rawPreviewBody}
                  </div>
                </div>
              </CardBody>
            </Card>
          ) : (
            <Card>
              <CardBody className="py-20 text-center text-ink-muted text-xs">
                {t("inbox.emptyDesc")}
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
