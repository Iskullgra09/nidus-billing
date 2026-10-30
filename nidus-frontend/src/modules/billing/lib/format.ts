/** Billing display helpers (API may store more precision than UI shows). */

function toNumber(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Always 2 decimal places (es-CR). */
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

export function formatMoneyInput(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "0.00";
  return n.toFixed(2);
}

/** Trim trailing zeros before %. */
export function formatPercent(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "—";
  const fixed = n.toFixed(2).replace(/\.?0+$/, "");
  return `${fixed}%`;
}

export function formatPercentInput(value: string | number | null | undefined): string {
  const n = toNumber(value);
  if (n == null) return "";
  return n.toFixed(2).replace(/\.?0+$/, "");
}
