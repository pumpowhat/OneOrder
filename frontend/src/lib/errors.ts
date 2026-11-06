import { ApiError } from "../api/client.ts";
import type { TranslationKey } from "../i18n/en.ts";

/** Message to show for a failed call: the backend's own text, or a hint when it is not running. */
export function errorMessage(err: unknown, t: (key: TranslationKey) => string): string {
  if (err instanceof ApiError) return err.status === 0 ? t("error.backend") : err.message;
  return err instanceof Error ? err.message : String(err);
}
