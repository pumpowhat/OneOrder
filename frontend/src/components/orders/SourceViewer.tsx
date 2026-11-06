import { useState } from "react";
import { Download } from "lucide-react";
import { getOrderSource, orderSourceFileUrl } from "../../api/orders.ts";
import { useApi } from "../../hooks/useApi.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { errorMessage } from "../../lib/errors.ts";
import { cn } from "../../lib/cn.ts";

/** The original photo, email or spreadsheet, shown as it was uploaded so it can be checked against the lines. */
export function SourceViewer({ orderId }: { orderId: string }) {
  const { t } = useI18n();
  const { data, error, loading } = useApi((signal) => getOrderSource(orderId, signal), [orderId]);
  const [zoom, setZoom] = useState(false);

  if (loading) return <p className="text-sm text-ink-muted p-5">{t("common.loading")}</p>;
  if (error || !data) return <p className="text-sm text-ink-muted p-5">{error ? errorMessage(error, t) : t("source.missing")}</p>;

  return (
    <div className="space-y-3 p-5">
      {data.kind === "image" && (
        <button
          type="button"
          onClick={() => setZoom((z) => !z)}
          aria-label={zoom ? t("source.fit") : t("source.zoom")}
          className={cn("block w-full rounded-lg border border-line overflow-auto bg-surface-2", zoom ? "max-h-[640px] cursor-zoom-out" : "cursor-zoom-in")}
        >
          <img
            src={orderSourceFileUrl(orderId)}
            alt={data.name ?? t("source.title")}
            className={cn("block", zoom ? "max-w-none w-[1400px]" : "w-full h-auto")}
          />
        </button>
      )}
      {data.kind === "text" && (
        <pre className="whitespace-pre-wrap break-words text-sm leading-relaxed font-sans bg-surface-2 border border-line rounded-lg p-4 max-h-[520px] overflow-auto">
          {data.text}
        </pre>
      )}
      {data.kind === "table" && (
        <div className="border border-line rounded-lg overflow-auto max-h-[520px]">
          <table className="w-full text-xs">
            <tbody>
              {data.rows.map((row, r) => (
                <tr key={r} className={cn("border-b border-line last:border-0", r === 0 && "bg-surface-2 font-semibold")}>
                  {row.map((cell, c) => (
                    <td key={c} className="px-3 py-1.5 whitespace-nowrap">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <a
        href={orderSourceFileUrl(orderId)}
        download={data.name ?? undefined}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-brand hover:underline"
      >
        <Download className="w-3.5 h-3.5" aria-hidden="true" />
        {data.name ?? t("source.download")}
      </a>
    </div>
  );
}
