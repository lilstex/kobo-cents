// Shared between the stock detail metric cards and the compare
// table, per docs/backend-architecture/01.md: "same metric categories
// and order as the stock detail page," which only means something if
// the same value actually formats the same way in both places.
export const CATEGORY_LABELS: Record<string, string> = {
  liquidity: "Liquidity",
  equity: "Equity",
  profitability: "Profitability",
  valuation_and_growth: "Valuation and Growth",
  dividends: "Dividends",
};

const PERCENT_METRICS = new Set([
  "net_profit_margin",
  "roe",
  "roic",
  "revenue_growth_rate",
  "dividend_yield",
]);
const RATIO_METRICS = new Set(["current_ratio", "quick_ratio", "pe_ratio"]);
// Absolute currency figures, company-wide scale (hundreds of millions
// or more), compact notation so a card reads "800M" instead of a
// long, hard-to-scan raw number; book_value is per-share and stays a
// plain small number instead.
const LARGE_SCALE_METRICS = new Set(["shareholders_equity", "free_cash_flow"]);

export function formatMetricValue(key: string, value: number | null): string {
  if (value === null) return "—";
  if (RATIO_METRICS.has(key)) return value.toFixed(key === "pe_ratio" ? 1 : 2);
  if (PERCENT_METRICS.has(key)) return `${(value * 100).toFixed(1)}%`;
  if (LARGE_SCALE_METRICS.has(key)) {
    return new Intl.NumberFormat(undefined, {
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value);
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
