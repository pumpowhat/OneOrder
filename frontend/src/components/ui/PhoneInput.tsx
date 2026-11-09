import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Globe2, Search } from "lucide-react";
import { useI18n } from "../../i18n/useI18n.ts";
import { PHONE_COUNTRIES, countryFlag, type PhoneCountry } from "../../lib/phoneCountries.ts";
import { splitCustomerPhone } from "../../lib/phone.ts";

interface Props {
  id: string;
  value: string;
  onChange: (value: string) => void;
  invalid?: boolean;
  describedBy?: string;
  disabled?: boolean;
  required?: boolean;
}

const PRIORITY = ["DK", "SE", "NO", "VN"];
const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase();

/** Searchable calling-code picker plus national-number input; stores one phone string. */
export function PhoneInput({ id, value, onChange, invalid, describedBy, disabled, required = true }: Props) {
  const { locale, t } = useI18n();
  const uid = useId();
  const listId = `${uid}-countries`;
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [preferredCountry, setPreferredCountry] = useState<string | null>(null);
  const parts = splitCustomerPhone(value, preferredCountry);
  const countries = useMemo(() => {
    const names = new Intl.DisplayNames([locale], { type: "region" });
    const english = new Intl.DisplayNames(["en"], { type: "region" });
    return PHONE_COUNTRIES.map((country) => ({ ...country, name: names.of(country.code) ?? country.code, english: english.of(country.code) ?? country.code }))
      .sort((a, b) => {
        const pa = PRIORITY.indexOf(a.code);
        const pb = PRIORITY.indexOf(b.code);
        return (pa < 0 ? PRIORITY.length : pa) - (pb < 0 ? PRIORITY.length : pb) || a.name.localeCompare(b.name, locale);
      });
  }, [locale]);
  const filtered = countries.filter((country) => normalize(`${country.name} ${country.english} ${country.code} ${country.dialCode}`).includes(normalize(query.trim())));
  const selectedName = countries.find((country) => country.code === parts.country?.code)?.name;

  const show = () => { setQuery(""); setActive(0); setOpen(true); };
  const close = () => { setOpen(false); trigger.current?.focus(); };
  const choose = (country: PhoneCountry) => {
    setPreferredCountry(country.code);
    onChange(country.dialCode + parts.nationalNumber.trim());
    close();
    // Continue entering the number after choosing a country.
    document.getElementById(id)?.focus();
  };

  useEffect(() => {
    if (!open) return;
    search.current?.focus();
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);

  useEffect(() => {
    if (open) document.getElementById(`${listId}-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [active, open, listId]);

  return (
    <div ref={root} className="relative flex items-start gap-2 w-full max-w-[420px]" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
    }}>
      <button
        ref={trigger}
        type="button"
        disabled={disabled}
        aria-label={`${t("phone.countryLabel")}${selectedName ? `: ${selectedName} ${parts.dialCode}` : parts.dialCode ? `: ${parts.dialCode}` : ""}`}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? `${uid}-picker` : undefined}
        title={selectedName ?? t("phone.countryLabel")}
        onClick={() => open ? close() : show()}
        onKeyDown={(event) => { if (event.key === "ArrowDown") { event.preventDefault(); show(); } }}
        className="flex shrink-0 items-center justify-between gap-2 h-9 w-32 sm:w-36 px-2.5 rounded-md border border-line-strong bg-surface text-sm hover:bg-surface-2 disabled:opacity-50"
      >
        {parts.country ? <span className="text-lg leading-none" aria-hidden="true">{countryFlag(parts.country.code)}</span> : <Globe2 className="w-4 h-4 text-ink-muted shrink-0" aria-hidden="true" />}
        <span className="flex-1 text-left tabular-nums truncate">{parts.dialCode || t("phone.codePlaceholder")}</span>
        <ChevronDown className="w-3.5 h-3.5 text-ink-muted shrink-0" aria-hidden="true" />
      </button>

      <input
        id={id}
        type="tel"
        inputMode="tel"
        autoComplete="tel-national"
        required={required}
        aria-required={required}
        aria-invalid={invalid}
        aria-describedby={describedBy}
        disabled={disabled}
        value={parts.nationalNumber}
        maxLength={64}
        placeholder={t("phone.numberPlaceholder")}
        onChange={(event) => {
          const entered = event.target.value;
          // Pasting a complete international number also updates its prefix selector.
          if (/^(\+|00)/.test(entered.trim())) {
            setPreferredCountry(null);
            onChange(entered);
          } else onChange(parts.dialCode + entered);
        }}
        className="min-w-0 flex-1 h-9 px-2.5 rounded-md border border-line-strong bg-surface text-sm tabular-nums disabled:opacity-50"
      />

      {open && (
        <div id={`${uid}-picker`} role="dialog" aria-label={t("phone.countryLabel")} className="absolute left-0 top-11 z-50 w-[min(20rem,calc(100vw-4rem))] rounded-lg border border-line-strong bg-surface shadow-lg overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-line">
            <Search className="w-4 h-4 text-ink-muted shrink-0" aria-hidden="true" />
            <input
              ref={search}
              type="search"
              role="combobox"
              aria-label={t("phone.search")}
              aria-autocomplete="list"
              aria-expanded="true"
              aria-controls={listId}
              aria-activedescendant={filtered[active] ? `${listId}-${active}` : undefined}
              value={query}
              placeholder={t("phone.search")}
              onChange={(event) => { setQuery(event.target.value); setActive(0); }}
              onKeyDown={(event) => {
                if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(); }
                else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                  event.preventDefault();
                  setActive((index) => filtered.length ? (index + (event.key === "ArrowDown" ? 1 : -1) + filtered.length) % filtered.length : 0);
                } else if (event.key === "Enter") {
                  event.preventDefault();
                  if (filtered[active]) choose(filtered[active]);
                }
              }}
              className="min-w-0 flex-1 bg-transparent text-sm h-8 outline-none"
            />
          </div>
          <div id={listId} role="listbox" aria-label={t("phone.countryLabel")} className="max-h-60 overflow-y-auto p-1">
            {filtered.map((country, index) => (
              <button
                key={country.code}
                id={`${listId}-${index}`}
                type="button"
                role="option"
                tabIndex={-1}
                aria-selected={parts.country?.code === country.code}
                onPointerDown={(event) => event.preventDefault()}
                onClick={() => choose(country)}
                className={`w-full flex items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm hover:bg-surface-2 ${index === active ? "bg-surface-2" : ""}`}
              >
                <span className="text-lg leading-none" aria-hidden="true">{countryFlag(country.code)}</span>
                <span className="flex-1 min-w-0 truncate">{country.name} <span className="text-xs text-ink-faint">{country.code}</span></span>
                <span className="text-xs text-ink-muted tabular-nums">{country.dialCode}</span>
                <span className="w-3.5">{parts.country?.code === country.code && <Check className="w-3.5 h-3.5 text-accent" aria-hidden="true" />}</span>
              </button>
            ))}
            {filtered.length === 0 && <p role="status" className="px-3 py-5 text-center text-sm text-ink-muted">{t("phone.noResults")}</p>}
          </div>
        </div>
      )}
    </div>
  );
}
