import { useEffect, useId, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { OrderCandidate } from "../../types/api.ts";

interface Props {
  value: string;
  candidates: OrderCandidate[];
  label: string;
  placeholder: string;
  disabled: boolean;
  onChange: (sku: string) => void;
}

/** Shows the matcher's three suggestions without restricting manual SKU entry. */
export function ProductCodeInput({ value, candidates, label, placeholder, disabled, onChange }: Props) {
  const id = useId();
  const root = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const options = candidates.slice(0, 3);
  const expanded = open && !disabled && options.length > 0;
  const show = () => { setActive(-1); setOpen(true); };
  const choose = (sku: string) => { onChange(sku); setOpen(false); setActive(-1); };

  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);

  return (
    <div ref={root} className="relative w-full max-w-[420px] min-w-0" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
    }}>
      <input
        type="text"
        role="combobox"
        aria-label={label}
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls={expanded ? `${id}-options` : undefined}
        aria-activedescendant={expanded && active >= 0 ? `${id}-${active}` : undefined}
        autoComplete="off"
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={show}
        onClick={show}
        onChange={(event) => { onChange(event.target.value.trim()); show(); }}
        onKeyDown={(event) => {
          if ((event.key === "ArrowDown" || event.key === "ArrowUp") && options.length) {
            event.preventDefault();
            setOpen(true);
            setActive((index) => !expanded || index < 0
              ? (event.key === "ArrowDown" ? 0 : options.length - 1)
              : (index + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length);
          } else if (event.key === "Enter" && expanded) {
            event.preventDefault();
            if (options[active]) choose(options[active].sku);
            else setOpen(false);
          } else if (event.key === "Escape" && expanded) {
            event.preventDefault();
            event.stopPropagation();
            setOpen(false);
          }
        }}
        className="h-8 w-full min-w-0 pl-2 pr-7 rounded-md border border-line-strong bg-surface text-sm font-mono disabled:opacity-50"
      />
      <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-2 top-2 w-4 h-4 text-ink-muted" />
      {expanded && (
        <div id={`${id}-options`} role="listbox" aria-label={label}
          className="absolute left-0 top-full mt-1 z-50 w-full rounded-md border border-line-strong bg-surface text-ink shadow-lg p-1">
          {options.map((candidate, index) => (
            <button key={candidate.sku} id={`${id}-${index}`} type="button" role="option" tabIndex={-1}
              aria-selected={value === candidate.sku}
              onPointerDown={(event) => event.preventDefault()}
              onPointerMove={() => setActive(index)}
              onClick={() => choose(candidate.sku)}
              className={`block w-full rounded px-2 py-2 text-left hover:bg-surface-2 ${index === active ? "bg-surface-2" : ""}`}>
              <span className="block text-sm font-mono break-all">{candidate.sku}</span>
              <span className="block text-xs text-ink-muted break-words">{candidate.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
