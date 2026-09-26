import { Fragment } from "react";
import { BucketChip } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";
import { CATEGORY_LABELS, formatMetricValue } from "@/lib/metricFormat";

type StockDetailResponse = components["schemas"]["StockDetailResponse"];

/** Desktop: a real table, ticker per column, per docs/backend-
 * architecture/01.md, "the same metric categories and order used on
 * the detail page." The first stock's category/metric structure is
 * the row list, every stock has the identical structure (the backend
 * builds it from the same fixed, ordered metric definitions for
 * every stock), so indexing by key across stocks is always safe. */
export function CompareTable({
  stocks,
  bestInComparison,
}: {
  stocks: StockDetailResponse[];
  bestInComparison: Record<string, string>;
}) {
  return (
    <table className="hidden w-full border-collapse text-xs sm:table">
      <thead>
        <tr>
          <th className="border-b border-border py-2 text-left font-mono text-[10px] uppercase tracking-wider text-muted">
            Metric
          </th>
          {stocks.map((stock) => (
            <th
              key={stock.ticker}
              className="border-b border-border py-2 text-left font-mono text-[10px] uppercase tracking-wider text-muted"
            >
              {stock.ticker}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        <tr>
          <td className="border-b border-border py-2.5 text-muted">Bucket</td>
          {stocks.map((stock) => (
            <td key={stock.ticker} className="border-b border-border py-2.5">
              {stock.bucket ? (
                <BucketChip variant={stock.bucket as "well" | "potential" | "under"} />
              ) : (
                "—"
              )}
            </td>
          ))}
        </tr>
        <tr>
          <td className="border-b border-border py-2.5 text-muted">Price</td>
          {stocks.map((stock) => (
            <td key={stock.ticker} className="border-b border-border py-2.5 font-mono font-semibold">
              <span className={isUp(stock.change_percent) ? "text-brand" : "text-down"}>
                {formatPrice(stock.price, stock.market as "NG" | "US")}
              </span>{" "}
              <span className="text-[10px] text-muted">
                {formatChangePercent(stock.change_percent)}
              </span>
            </td>
          ))}
        </tr>
        {stocks[0]?.categories.map((category) => (
          <Fragment key={category.category}>
            <tr>
              <td colSpan={stocks.length + 1} className="pb-1 pt-4 text-[11px] font-bold text-text">
                {CATEGORY_LABELS[category.category] ?? category.category}
              </td>
            </tr>
            {category.metrics.map((metric) => (
              <tr key={metric.key}>
                <td className="border-b border-border py-2 text-muted">{metric.label}</td>
                {stocks.map((stock) => {
                  const stockMetric = stock.categories
                    .find((c) => c.category === category.category)
                    ?.metrics.find((m) => m.key === metric.key);
                  const isBest = bestInComparison[metric.key] === stock.ticker;
                  return (
                    <td
                      key={stock.ticker}
                      className={`border-b border-border py-2 font-mono font-semibold ${
                        isBest ? "text-brand" : "text-text"
                      }`}
                    >
                      {formatMetricValue(metric.key, stockMetric?.value ?? null)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
