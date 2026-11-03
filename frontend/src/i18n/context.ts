import { createContext } from "react";
import type { TranslationKey } from "./en.ts";

export type Locale = "en" | "vi";

export interface I18nContextType {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
}

export type I18nContextValue = I18nContextType;

export const I18nContext = createContext<I18nContextType | null>(null);
