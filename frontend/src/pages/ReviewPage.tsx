import { useState, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router";
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  History,
  Check,
  Building2,
  Calendar,
  FileText,
} from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { MockDataBanner } from "../components/ui/MockDataBanner";
import { Card, CardHeader, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ConfidenceBar } from "../components/ui/ConfidenceBar";
import { Segmented } from "../components/ui/Segmented";
import { useToast } from "../components/ui/useToast";
import { useI18n } from "../i18n/useI18n";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { formatIsoDate, formatTimestamp } from "../lib/format";
import { cn } from "../lib/cn";
import { MOCK_ORDERS } from "../mocks/orders";
import type { Order, AuditLogEntry, OrderStatus } from "../types/api";
import type { TranslationKey } from "../i18n/en";

const STATUS_KEYS: Record<OrderStatus, TranslationKey> = {
  draft: "common.draft",
  approved: "common.approved",
  planned: "common.planned",
  confirmed: "common.confirmedStatus",
};

const STATUS_TONES: Record<OrderStatus, "neutral" | "brand" | "success" | "warn" | "danger" | "info"> = {
  draft: "warn",
  approved: "success",
  planned: "brand",
  confirmed: "info",
};

export default function ReviewPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { pushToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  useDocumentTitle(t("review.title"));

  const initialOrderId = searchParams.get("orderId") || MOCK_ORDERS[0].id;
  const [selectedOrderId, setSelectedOrderId] = useState<string>(initialOrderId);

  // Store orders in local state so edits, confirmations and approvals persist in memory
  const [orders, setOrders] = useState<Order[]>(MOCK_ORDERS);

  const activeOrder = useMemo(() => {
    return orders.find((o) => o.id === selectedOrderId) || orders[0];
  }, [orders, selectedOrderId]);

  // Sync url param when order changes
  const handleSelectOrder = (orderId: string) => {
    setSelectedOrderId(orderId);
    setSearchParams({ orderId });
  };

  const flaggedCount = useMemo(() => {
    return activeOrder.lines.filter((l) => l.needs_review && !l.confirmed).length;
  }, [activeOrder]);

  const canApprove = flaggedCount === 0 && activeOrder.status === "draft";
  const isApproved = activeOrder.status === "approved" || activeOrder.status === "planned" || activeOrder.status === "confirmed";

  // Action: Confirm a specific line
  const handleConfirmLine = (lineIndex: number) => {
    setOrders((prevOrders) =>
      prevOrders.map((ord) => {
        if (ord.id !== activeOrder.id) return ord;

        const targetLine = ord.lines.find((l) => l.line_index === lineIndex);
        if (!targetLine) return ord;

        const updatedLines = ord.lines.map((l) =>
          l.line_index === lineIndex
            ? { ...l, confirmed: true, needs_review: false }
            : l
        );

        const newAuditLog: AuditLogEntry = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          action: "edit_line",
          user: "sales_desk",
          payload_before: { line_index: lineIndex, confirmed: targetLine.confirmed },
          payload_after: { line_index: lineIndex, confirmed: true, needs_review: false },
        };

        return {
          ...ord,
          lines: updatedLines,
          audit_logs: [newAuditLog, ...ord.audit_logs],
        };
      })
    );

    pushToast({
      title: t("common.confirm"),
      description: `Line #${lineIndex} verified and confirmed.`,
      tone: "success",
    });
  };

  // Action: Change candidate SKU for a line
  const handleSelectCandidateSku = (lineIndex: number, newSku: string) => {
    setOrders((prevOrders) =>
      prevOrders.map((ord) => {
        if (ord.id !== activeOrder.id) return ord;

        const targetLine = ord.lines.find((l) => l.line_index === lineIndex);
        if (!targetLine) return ord;

        const selectedCandidate = targetLine.candidates.find((c) => c.sku === newSku);
        const oldSku = targetLine.matched_sku;

        const updatedLines = ord.lines.map((l) =>
          l.line_index === lineIndex
            ? {
                ...l,
                matched_sku: newSku,
                description: selectedCandidate?.description || l.description,
                match_score: selectedCandidate?.score ?? l.match_score,
                confirmed: true,
                ambiguous: false,
                needs_review: false,
              }
            : l
        );

        const newAuditLog: AuditLogEntry = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          action: "edit_line",
          user: "sales_desk",
          payload_before: { line_index: lineIndex, matched_sku: oldSku },
          payload_after: { line_index: lineIndex, matched_sku: newSku, confirmed: true },
        };

        return {
          ...ord,
          lines: updatedLines,
          audit_logs: [newAuditLog, ...ord.audit_logs],
        };
      })
    );

    pushToast({
      title: "SKU Selected",
      description: `Line #${lineIndex} updated to SKU ${newSku}.`,
      tone: "info",
    });
  };

  // Action: Edit quantity
  const handleEditQuantity = (lineIndex: number, newQty: number) => {
    if (isNaN(newQty) || newQty <= 0) return;

    setOrders((prevOrders) =>
      prevOrders.map((ord) => {
        if (ord.id !== activeOrder.id) return ord;

        const targetLine = ord.lines.find((l) => l.line_index === lineIndex);
        if (!targetLine || targetLine.quantity === newQty) return ord;

        const oldQty = targetLine.quantity;
        const updatedLines = ord.lines.map((l) =>
          l.line_index === lineIndex
            ? { ...l, quantity: newQty, confirmed: true, needs_review: false }
            : l
        );

        const newAuditLog: AuditLogEntry = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          action: "edit_line",
          user: "sales_desk",
          payload_before: { line_index: lineIndex, quantity: oldQty },
          payload_after: { line_index: lineIndex, quantity: newQty },
        };

        return {
          ...ord,
          lines: updatedLines,
          audit_logs: [newAuditLog, ...ord.audit_logs],
        };
      })
    );

    pushToast({
      title: "Quantity Updated",
      description: `Line #${lineIndex} quantity adjusted to ${newQty}.`,
      tone: "info",
    });
  };

  // Action: Approve Order
  const handleApproveOrder = () => {
    setOrders((prevOrders) =>
      prevOrders.map((ord) => {
        if (ord.id !== activeOrder.id) return ord;

        const newAuditLog: AuditLogEntry = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          action: "approve",
          user: "sales_desk",
          payload_before: { status: ord.status },
          payload_after: { status: "approved" },
        };

        return {
          ...ord,
          status: "approved",
          needs_review: false,
          audit_logs: [newAuditLog, ...ord.audit_logs],
        };
      })
    );

    pushToast({
      title: t("common.approved"),
      description: t("review.approveSuccess", { id: activeOrder.id }),
      tone: "success",
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("review.title")}
        subtitle={t("review.subtitle")}
        actions={
          <div className="flex items-center gap-2">
            {isApproved && (
              <Button
                variant="primary"
                onClick={() => navigate(`/plan?orderId=${activeOrder.id}`)}
              >
                <span>{t("review.proceedToPlanBtn")}</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            )}
            {!isApproved && (
              <Button
                variant="primary"
                disabled={!canApprove}
                onClick={handleApproveOrder}
              >
                <Check className="w-4 h-4 mr-1.5" />
                {t("review.approveBtn")}
              </Button>
            )}
          </div>
        }
      />

      <MockDataBanner />

      {/* Order Switcher Tabs */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-ink-muted mr-1">
          {t("review.selectOrder")}
        </span>
        <Segmented<string>
          size="sm"
          value={activeOrder.id}
          onChange={handleSelectOrder}
          options={orders.map((o) => ({
            value: o.id,
            label: `${o.customer?.split(" ")[0]} (${o.id})`,
          }))}
        />
      </div>

      {/* Order Header Summary Card */}
      <Card>
        <CardBody className="p-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-line">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-ink">{activeOrder.customer}</h2>
                <Badge tone={STATUS_TONES[activeOrder.status]}>
                  {t(STATUS_KEYS[activeOrder.status])}
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-xs text-ink-muted">
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-brand" />
                  {activeOrder.delivery_site}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-brand" />
                  {t("common.requestedDate")}: {formatIsoDate(activeOrder.requested_date)}
                </span>
                <span className="flex items-center gap-1.5 font-mono text-ink-faint">
                  <FileText className="w-3.5 h-3.5" />
                  {activeOrder.source_name}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-2 border border-line text-ink font-semibold">
                ID: {activeOrder.id}
              </span>
            </div>
          </div>

          {/* Warnings Banner if any */}
          {activeOrder.warnings.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-warn-soft/60 border border-warn/30 space-y-1">
              {activeOrder.warnings.map((warn, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-warn font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{warn}</span>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Governance & Human-in-the-Loop Threshold Banner */}
      <div
        className={cn(
          "p-4 rounded-xl border flex items-center justify-between gap-4",
          flaggedCount > 0
            ? "bg-warn-soft/40 border-warn/30 text-ink"
            : "bg-success-soft/40 border-success/30 text-ink"
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "w-9 h-9 rounded-xl flex items-center justify-center shrink-0",
              flaggedCount > 0 ? "bg-warn-soft text-warn" : "bg-success-soft text-success"
            )}
          >
            {flaggedCount > 0 ? (
              <ShieldAlert className="w-5 h-5" />
            ) : (
              <CheckCircle2 className="w-5 h-5" />
            )}
          </div>
          <div>
            <p className="text-xs font-bold text-ink">
              {flaggedCount > 0
                ? t("review.flaggedPending", { count: flaggedCount })
                : t("review.allConfirmed")}
            </p>
            <p className="text-xs text-ink-muted mt-0.5">
              {t("review.governanceBanner")}
            </p>
          </div>
        </div>

        {flaggedCount === 0 && !isApproved && (
          <Button variant="primary" size="sm" onClick={handleApproveOrder}>
            <Check className="w-3.5 h-3.5 mr-1" />
            {t("review.approveBtn")}
          </Button>
        )}
      </div>

      {/* Interactive Order Lines Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="text-sm font-bold text-ink">
              Order Materials ({activeOrder.lines.length} lines)
            </h3>
            <span className="text-xs text-ink-muted">
              Auto-saved to local draft state
            </span>
          </div>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-surface-2 border-b border-line text-ink-muted font-semibold">
                <th className="py-2.5 px-4 w-10 text-center">{t("review.lineColIndex")}</th>
                <th className="py-2.5 px-4 min-w-[280px]">{t("review.lineColDesc")}</th>
                <th className="py-2.5 px-4 w-24">{t("review.lineColQty")}</th>
                <th className="py-2.5 px-4 w-20">{t("review.lineColUnit")}</th>
                <th className="py-2.5 px-4 min-w-[240px]">{t("review.lineColSku")}</th>
                <th className="py-2.5 px-4 w-36">{t("review.lineColConfidence")}</th>
                <th className="py-2.5 px-4 w-28 text-right">{t("review.lineColAction")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {activeOrder.lines.map((line) => {
                const isFlagged = line.needs_review && !line.confirmed;

                return (
                  <tr
                    key={line.line_index}
                    className={cn(
                      "transition-colors",
                      isFlagged
                        ? "bg-warn-soft/20 border-l-4 border-l-warn"
                        : "hover:bg-surface-2/40 border-l-4 border-l-transparent"
                    )}
                  >
                    {/* Index */}
                    <td className="py-3 px-4 text-center font-mono font-bold text-ink-muted">
                      {line.line_index}
                    </td>

                    {/* Description + Source text snippet */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-ink">{line.description}</div>
                      {line.source_text && (
                        <div className="text-[11px] font-mono text-ink-muted mt-1 bg-surface-2/80 px-2 py-0.5 rounded border border-line/60 inline-block">
                          {line.source_text}
                        </div>
                      )}
                      {line.ambiguous && !line.confirmed && (
                        <div className="mt-1 flex items-center gap-1 text-[11px] text-warn font-medium">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Close match scores — select correct candidate SKU</span>
                        </div>
                      )}
                    </td>

                    {/* Inline Editable Quantity */}
                    <td className="py-3 px-4">
                      <input
                        type="number"
                        min="1"
                        value={line.quantity}
                        onChange={(e) =>
                          handleEditQuantity(line.line_index, parseFloat(e.target.value))
                        }
                        className="w-20 h-7 px-2 font-mono text-xs bg-surface border border-line-strong rounded text-ink focus:outline-brand"
                      />
                    </td>

                    {/* Unit */}
                    <td className="py-3 px-4 font-mono text-ink-muted uppercase">
                      {line.unit || "—"}
                    </td>

                    {/* Matched SKU with candidate selector dropdown */}
                    <td className="py-3 px-4">
                      {line.candidates.length > 1 ? (
                        <div className="space-y-1">
                          <select
                            value={line.matched_sku || ""}
                            onChange={(e) =>
                              handleSelectCandidateSku(line.line_index, e.target.value)
                            }
                            className={cn(
                              "w-full h-7 px-2 font-mono text-xs rounded border text-ink bg-surface cursor-pointer",
                              isFlagged
                                ? "border-warn focus:outline-warn"
                                : "border-line-strong focus:outline-brand"
                            )}
                          >
                            {line.candidates.map((cand) => (
                              <option key={cand.sku} value={cand.sku}>
                                {cand.sku} ({cand.score}%) — {cand.description.slice(0, 30)}...
                              </option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <div>
                          <span className="font-mono font-semibold text-ink">
                            {line.matched_sku || "—"}
                          </span>
                          {line.match_score && (
                            <span className="font-mono text-[10px] text-ink-faint ml-2">
                              ({line.match_score}%)
                            </span>
                          )}
                        </div>
                      )}
                    </td>

                    {/* Confidence */}
                    <td className="py-3 px-4">
                      <ConfidenceBar value={line.confidence} threshold={0.85} />
                    </td>

                    {/* Action: Confirm button or Verified badge */}
                    <td className="py-3 px-4 text-right">
                      {line.confirmed ? (
                        <Badge tone="success" className="px-2 py-0.5">
                          <Check className="w-3 h-3 mr-0.5" />
                          {t("review.confirmedBadge")}
                        </Badge>
                      ) : (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleConfirmLine(line.line_index)}
                          className="h-7 text-xs bg-warn-soft text-warn border-warn/30 hover:bg-warn-soft/80"
                        >
                          {t("review.confirmLineBtn")}
                        </Button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Audit Trail (Immutable history log) */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-brand" />
            <h3 className="text-sm font-bold text-ink">
              {t("review.auditTrailTitle")}
            </h3>
          </div>
          <span className="text-xs text-ink-muted">
            {t("review.auditTrailSubtitle")}
          </span>
        </CardHeader>

        <CardBody className="p-0">
          <div className="divide-y divide-line">
            {activeOrder.audit_logs.map((log) => {
              return (
                <div
                  key={log.id}
                  className="p-4 flex items-start justify-between gap-4 text-xs hover:bg-surface-2/30 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        tone={
                          log.action === "approve"
                            ? "success"
                            : log.action === "edit_line"
                              ? "brand"
                              : "neutral"
                        }
                      >
                        {log.action}
                      </Badge>
                      <span className="font-mono font-medium text-ink">
                        @{log.user}
                      </span>
                      <span className="text-ink-muted">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>

                    <div className="font-mono text-[11px] text-ink-muted bg-surface-2 px-2.5 py-1 rounded border border-line inline-block">
                      {JSON.stringify(log.payload_after || log.payload_before)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
