import { createContext } from "react";
import type { TranslationKey } from "./en.ts";

export type Locale = "en" | "vi";

export interface I18nContextValue {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue | null>(null);
