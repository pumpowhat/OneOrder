const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

export function formatPercent(value0to1: number): string {
  const clamped = Math.max(0, Math.min(1, value0to1));
  return `${Math.round(clamped * 100)}%`;
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

export function formatWeightKg(kg: number): string {
  return `${formatNumber(kg)} kg`;
}

export function formatIsoDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  // Matches YYYY-MM-DD
  const parts = dateStr.slice(0, 10).split("-");
  if (parts.length !== 3) return dateStr;
  const year = parts[0];
  const monthIdx = parseInt(parts[1], 10) - 1;
  const day = parts[2].padStart(2, "0");
  const month = MONTH_NAMES[monthIdx] || parts[1];
  return `${day} ${month} ${year}`;
}

export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    const day = String(d.getDate()).padStart(2, "0");
    const month = MONTH_NAMES[d.getMonth()] || "—";
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, "0");
    const minutes = String(d.getMinutes()).padStart(2, "0");
    return `${day} ${month} ${year}, ${hours}:${minutes}`;
  } catch {
    return "—";
  }
}
