/** Display helpers for billing money / tax rates (API may store more precision). */

function toNumber(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Money for tables/PDF-like UI: always 2 fraction digits. */
export function formatMoney(
  value: string | number | null | undefined,
  options?: { currency?: string; withCurrency?: boolean },
): string {
  const n = toNumber(value);
  if (n == null) return "—";
  const amount = new Intl.NumberFormat("es-CR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
  if (options?.withCurrency && options.currency) {
    return `${amount} ${options.currency}`;
  }
  return amount;
}

/** Compact money string for form inputs (no grouping). */
export function formatMoneyInput(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "0.00";
  return n.toFixed(2);
}

/** Tax rate for tables: trim trailing zeros, append %. */
export function formatPercent(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "—";
  const fixed = n.toFixed(2).replace(/\.?0+$/, "");
  return `${fixed}%`;
}

/** Tax rate for form inputs. */
export function formatPercentInput(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "";
  return n.toFixed(2).replace(/\.?0+$/, "");
}
