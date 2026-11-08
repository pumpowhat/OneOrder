import { FileImage, FileSpreadsheet, FileText, Mail } from "lucide-react";
import { listInbox } from "../../api/inbox.ts";
import { useApi } from "../../hooks/useApi.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { Button } from "../ui/Button.tsx";
import { Card, CardHeader } from "../ui/Card.tsx";
import type { SourceType } from "../../types/api.ts";
import { useUpload } from "./useUpload.ts";

const ICON: Record<SourceType, typeof Mail> = { image: FileImage, pdf: FileText, excel: FileSpreadsheet, email: Mail };

/** The demo mailbox: pick a message and it goes through the same reading pipeline as an upload. */
export function InboxPanel({ defaultOpen }: { defaultOpen: boolean }) {
  const { t } = useI18n();
  const { data } = useApi((signal) => listInbox(signal), []);
  const { importItem, busy } = useUpload();
  const items = data ?? [];
  if (items.length === 0) return null;

  return (
    <details open={defaultOpen} className="group">
      <Card>
        <summary className="list-none cursor-pointer">
          <CardHeader>
            <h2 className="text-sm font-semibold">{t("inbox.title")}</h2>
            <span className="text-xs text-ink-muted">{t("inbox.count", { n: items.length })}</span>
          </CardHeader>
        </summary>
        <ul className="divide-y divide-line">
          {items.map((item) => {
            const Icon = ICON[item.kind];
            return (
              <li key={item.id} className="flex items-center gap-3 px-5 py-2.5">
                <Icon className="w-4 h-4 text-ink-faint shrink-0" aria-hidden="true" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{item.filename}</div>
                  {item.preview && <div className="text-xs text-ink-muted truncate">{item.preview}</div>}
                </div>
                <Button size="sm" disabled={busy} onClick={() => void importItem(item.id, item.filename)}>
                  {t("inbox.import")}
                </Button>
              </li>
            );
          })}
        </ul>
      </Card>
    </details>
  );
}
