import { BucketChip, Card } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";
import { CATEGORY_LABELS, formatMetricValue } from "@/lib/metricFormat";

type StockDetailResponse = components["schemas"]["StockDetailResponse"];

/** Mobile: the same rows, stacked one stock at a time rather than
 * side by side, per docs/frontend-architecture/06-design.md's compare
 * mockup caption. The best-in-comparison highlight still applies
 * regardless of which stock's card a value happens to sit in. */
export function CompareStack({
  stocks,
  bestInComparison,
}: {
  stocks: StockDetailResponse[];
  bestInComparison: Record<string, string>;
}) {
  return (
    <div className="flex flex-col gap-4 sm:hidden">
      {stocks.map((stock) => (
        <Card key={stock.ticker}>
          <div className="mb-2 flex items-center justify-between">
            <div>
              <div className="text-sm font-bold text-text">{stock.ticker}</div>
              <div className="text-[11px] text-muted">{stock.company_name}</div>
            </div>
            {stock.bucket ? (
              <BucketChip variant={stock.bucket as "well" | "potential" | "under"} />
            ) : null}
          </div>

          <div className="mb-3 flex items-baseline gap-2">
            <span
              className={`font-mono text-sm font-bold ${
                isUp(stock.change_percent) ? "text-brand" : "text-down"
              }`}
            >
              {formatPrice(stock.price, stock.market as "NG" | "US")}
            </span>
            <span className="font-mono text-[11px] text-muted">
              {formatChangePercent(stock.change_percent)}
            </span>
          </div>

          {stock.categories.map((category) => (
            <div key={category.category} className="mb-2">
              <div className="mb-1 text-[11px] font-bold text-text">
                {CATEGORY_LABELS[category.category] ?? category.category}
              </div>
              {category.metrics.map((metric) => {
                const isBest = bestInComparison[metric.key] === stock.ticker;
                return (
                  <div
                    key={metric.key}
                    className="flex items-center justify-between border-b border-border py-1 text-xs last:border-b-0"
                  >
                    <span className="text-muted">{metric.label}</span>
                    <span
                      className={`font-mono font-semibold ${isBest ? "text-brand" : "text-text"}`}
                    >
                      {formatMetricValue(metric.key, metric.value)}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}
        </Card>
      ))}
    </div>
  );
}
