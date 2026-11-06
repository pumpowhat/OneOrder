import { useCallback, useState } from "react";
import { useNavigate } from "react-router";
import { uploadOrder } from "../../api/orders.ts";
import { errorMessage } from "../../lib/errors.ts";
import { useI18n } from "../../i18n/useI18n.ts";
import { useToast } from "../ui/useToast.ts";

export const ACCEPTED_FILES = ".jpg,.jpeg,.png,.webp,.xlsx,.txt,.eml";

/** Upload one file for OCR; on success open the new order so the clerk can review it right away. */
export function useUpload() {
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const { pushToast } = useToast();
  const { t } = useI18n();

  const upload = useCallback(
    async (file: File) => {
      setBusy(true);
      try {
        const order = await uploadOrder(file);
        pushToast({ tone: "success", title: t("upload.done"), description: file.name });
        navigate(`/orders/${order.id}`);
      } catch (err) {
        pushToast({ tone: "danger", title: t("upload.failed"), description: errorMessage(err, t) });
      } finally {
        setBusy(false);
      }
    },
    [navigate, pushToast, t],
  );

  return { upload, busy };
}
