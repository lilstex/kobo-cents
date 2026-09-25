import Link from "next/link";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";

type StockSummary = components["schemas"]["StockSummary"];

/** The mobile list row, per docs/frontend-architecture/06-design.md:
 * ticker bold, company name muted underneath, price and change in
 * JetBrains Mono on the right, brand-green up, down-red down. */
export function StockRow({ stock }: { stock: StockSummary }) {
  const up = isUp(stock.change_percent);
  return (
    <Link
      href={`/app/stocks/${stock.ticker}`}
      className="flex items-center justify-between border-b border-border py-2.5"
    >
      <div>
        <div className="text-sm font-bold text-text">{stock.ticker}</div>
        <div className="mt-0.5 text-[11.5px] text-muted">{stock.company_name}</div>
      </div>
      <div className="text-right">
        <div className="font-mono text-[13.5px] font-semibold text-text">
          {formatPrice(stock.price, stock.market as "NG" | "US")}
        </div>
        <div className={`font-mono text-[11.5px] font-semibold ${up ? "text-brand" : "text-down"}`}>
          {formatChangePercent(stock.change_percent)}
        </div>
      </div>
    </Link>
  );
}
