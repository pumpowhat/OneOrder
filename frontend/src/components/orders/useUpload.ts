import { useCallback, useState } from "react";
import { useNavigate } from "react-router";
import { importInboxItem } from "../../api/inbox.ts";
import { uploadOrder, uploadOrderText } from "../../api/orders.ts";
import { errorMessage } from "../../lib/errors.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { useToast } from "../ui/useToast.ts";

export const ACCEPTED_FILES = ".jpg,.jpeg,.png,.webp,.xlsx,.txt,.eml";

type Source = { file: File } | { text: string } | { inboxId: string };

/** Read one input (file, pasted email or sample inbox item); on success open the new order for review. */
export function useUpload() {
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const { pushToast } = useToast();
  const { t } = useI18n();

  const start = useCallback(
    async (source: Source, label: string) => {
      setBusy(true);
      try {
        const order =
          "file" in source
            ? await uploadOrder(source.file)
            : "text" in source
              ? await uploadOrderText(source.text)
              : await importInboxItem(source.inboxId);
        pushToast({ tone: "success", title: t("upload.done"), description: label });
        navigate(`/orders/${order.id}`);
      } catch (err) {
        pushToast({ tone: "danger", title: t("upload.failed"), description: errorMessage(err, t) });
      } finally {
        setBusy(false);
      }
    },
    [navigate, pushToast, t],
  );

  const upload = useCallback((file: File) => start({ file }, file.name), [start]);
  const uploadText = useCallback((text: string) => start({ text }, t("upload.pastedEmail")), [start, t]);
  const importItem = useCallback((id: string, filename: string) => start({ inboxId: id }, filename), [start]);

  return { upload, uploadText, importItem, busy };
}
