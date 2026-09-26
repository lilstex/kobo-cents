// Shared, tiny formatting used wherever a price or a percentage
// change renders, per docs/frontend-architecture/01.md: JetBrains
// Mono, --brand for up, --down for down, consistently, not
// reformatted slightly differently in each place it appears.

export function formatPrice(price: number | null, market: "NG" | "US"): string {
  if (price === null) return "—";
  const symbol = market === "NG" ? "₦" : "$";
  return `${symbol}${price.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatChangePercent(changePercent: number | null): string {
  if (changePercent === null) return "—";
  const arrow = changePercent >= 0 ? "↑" : "↓";
  return `${arrow} ${Math.abs(changePercent).toFixed(1)}%`;
}

export function isUp(changePercent: number | null): boolean {
  return (changePercent ?? 0) >= 0;
}
