import { useState, useCallback, useMemo, type ReactNode } from "react";
import { I18nContext, type Locale } from "./context.ts";
import { en, type TranslationKey } from "./en.ts";
import { vi } from "./vi.ts";
import { readStorage, writeStorage } from "../lib/storage.ts";

const STORAGE_KEY = "oneorder.locale";

const DICTIONARIES = {
  en,
  vi,
};

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = readStorage(STORAGE_KEY);
    return saved === "vi" || saved === "en" ? saved : "vi";
  });

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    writeStorage(STORAGE_KEY, next);
  }, []);

  const t = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>): string => {
      const dict = DICTIONARIES[locale] || DICTIONARIES.en;
      let text = dict[key] ?? DICTIONARIES.en[key] ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          text = text.replaceAll(`{${k}}`, String(v));
        }
      }
      return text;
    },
    [locale],
  );

  const value = useMemo(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
