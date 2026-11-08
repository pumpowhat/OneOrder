import { PHONE_COUNTRIES } from "./phoneCountries.ts";

/** Match backend syntax validation; this does not verify ownership or guess a country. */
export function isValidCustomerPhone(value: string): boolean {
  const raw = value.trim();
  if (!raw || raw.length > 64 || !/^\+?[0-9\s().-]+$/.test(raw)) return false;
  const compact = raw.replace(/[\s().-]/g, "").replace(/^00/, "+");
  const digits = compact.replace(/^\+/, "");
  return /^[0-9]{7,15}$/.test(digits) && !(compact.startsWith("+") && digits.startsWith("0"));
}

/** Split a written international prefix without inventing one for national numbers.
 * Shared prefixes (+1, +44, etc.) do not identify a country without the user's choice.
 */
export function splitCustomerPhone(value: string, preferredCountry?: string | null) {
  const compact = value.trim().replace(/[\s().-]/g, "").replace(/^00/, "+");
  if (!compact.startsWith("+")) return { dialCode: "", nationalNumber: value, country: undefined };
  const candidates = PHONE_COUNTRIES.filter((country) => compact.startsWith(country.dialCode));
  const dialCode = candidates.reduce((longest, country) => country.dialCode.length > longest.length ? country.dialCode : longest, "");
  if (!dialCode) return { dialCode: "", nationalNumber: value, country: undefined };
  const matches = candidates.filter((country) => country.dialCode === dialCode);
  const country = matches.find((item) => item.code === preferredCountry) ?? (matches.length === 1 ? matches[0] : undefined);
  return { dialCode, nationalNumber: compact.slice(dialCode.length), country };
}
