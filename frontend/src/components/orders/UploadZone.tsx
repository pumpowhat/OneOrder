import { useRef, useState, type DragEvent } from "react";
import { FileUp, Loader2 } from "lucide-react";
import { Button } from "../ui/Button.tsx";
import { useI18n } from "../../i18n/useI18n.ts";
import { cn } from "../../lib/cn.ts";
import { ACCEPTED_FILES, useUpload } from "./useUpload.ts";

/** Drag a photo, spreadsheet or email here, or click to choose one. */
export function UploadZone() {
  const { t } = useI18n();
  const { upload, busy } = useUpload();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const pick = (files: FileList | null) => {
    const file = files?.[0];
    if (file) void upload(file);
    if (input.current) input.current.value = "";
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    if (!busy) pick(event.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cn(
        "rounded-card border-2 border-dashed px-6 py-8 flex flex-col items-center text-center gap-3 transition-colors",
        over ? "border-accent bg-accent-soft" : "border-line-strong bg-surface",
      )}
    >
      <div className="w-10 h-10 rounded-full bg-accent-soft text-accent-ink flex items-center justify-center">
        {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileUp className="w-5 h-5" />}
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium">{busy ? t("upload.processing") : t("upload.title")}</p>
        <p className="text-xs text-ink-muted">{t("upload.hint")}</p>
      </div>
      <input
        ref={input}
        type="file"
        accept={ACCEPTED_FILES}
        className="sr-only"
        aria-label={t("upload.button")}
        onChange={(e) => pick(e.target.files)}
        tabIndex={-1}
      />
      <Button variant="accent" disabled={busy} onClick={() => input.current?.click()}>
        {busy ? t("upload.processing") : t("upload.button")}
      </Button>
    </div>
  );
}

/** Compact version for page headers. */
export function UploadButton({ variant = "accent" }: { variant?: "accent" | "primary" }) {
  const { t } = useI18n();
  const { upload, busy } = useUpload();
  const input = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={input}
        type="file"
        accept={ACCEPTED_FILES}
        className="sr-only"
        aria-label={t("upload.button")}
        tabIndex={-1}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void upload(file);
          e.target.value = "";
        }}
      />
      <Button variant={variant} disabled={busy} onClick={() => input.current?.click()}>
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileUp className="w-4 h-4" />}
        {busy ? t("upload.processing") : t("upload.button")}
      </Button>
    </>
  );
}
