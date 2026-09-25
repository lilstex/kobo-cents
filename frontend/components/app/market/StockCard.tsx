import Link from "next/link";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";

type StockSummary = components["schemas"]["StockSummary"];

/** The tablet/desktop grid card, per docs/frontend-architecture/
 * 06-design.md: same numbers as StockRow, a card treatment instead
 * of a list row once there's room for a multi-column grid. */
export function StockCard({ stock }: { stock: StockSummary }) {
  const up = isUp(stock.change_percent);
  return (
    <Link
      href={`/app/stocks/${stock.ticker}`}
      className="rounded-lg border border-border bg-surface p-3 hover:border-text"
    >
      <div className="text-sm font-bold text-text">{stock.ticker}</div>
      <div className="mt-0.5 text-[11.5px] text-muted">{stock.sector}</div>
      <div className="mt-2 font-mono text-[13.5px] font-semibold text-text">
        {formatPrice(stock.price, stock.market as "NG" | "US")}
      </div>
      <div className={`font-mono text-[11.5px] font-semibold ${up ? "text-brand" : "text-down"}`}>
        {formatChangePercent(stock.change_percent)}
      </div>
    </Link>
  );
}
