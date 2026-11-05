/** Billing display helpers (API may store more precision than UI shows). */

/** Parse amounts typed as `1234.56`, `1234,56`, or `1.234,56`. */
export function parseMoney(value: string | number | null | undefined): number | null {
  return toNumber(value);
}

function toNumber(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const raw = value.trim();
  if (!raw) return null;
  let normalized = raw;
  if (raw.includes(",") && raw.includes(".")) {
    // Assume last separator is decimal (es-CR / en-US mixed).
    const lastComma = raw.lastIndexOf(",");
    const lastDot = raw.lastIndexOf(".");
    if (lastComma > lastDot) {
      normalized = raw.replace(/\./g, "").replace(",", ".");
    } else {
      normalized = raw.replace(/,/g, "");
    }
  } else if (raw.includes(",")) {
    normalized = raw.replace(/\./g, "").replace(",", ".");
  }
  const n = Number(normalized);
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
