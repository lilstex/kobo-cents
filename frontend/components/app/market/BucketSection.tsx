import { BucketChip } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { StockCard } from "@/components/app/market/StockCard";
import { StockRow } from "@/components/app/market/StockRow";

type StockSummary = components["schemas"]["StockSummary"];
type Bucket = "well" | "potential" | "under";

/** One bucket's worth of the market overview: the chip-plus-count
 * header from docs/frontend-architecture/06-design.md, then the same
 * stocks rendered two ways, CSS deciding which one is visible rather
 * than a JS breakpoint listener, the same pattern components/app/
 * AppNav.tsx already established in Phase 3. A bucket with nothing in
 * it renders nothing at all, never an empty header. */
export function BucketSection({
  bucket,
  total,
  stocks,
}: {
  bucket: Bucket;
  total: number;
  stocks: StockSummary[];
}) {
  if (total === 0) return null;

  return (
    <section className="mb-6">
      <div className="mb-2 mt-4 flex items-center gap-2">
        <BucketChip variant={bucket} />
        <span className="font-mono text-[11px] font-semibold text-muted">{total}</span>
      </div>

      <div className="sm:hidden">
        {stocks.map((stock) => (
          <StockRow key={stock.ticker} stock={stock} />
        ))}
      </div>

      <div className="hidden gap-3 sm:grid sm:grid-cols-2 lg:grid-cols-3">
        {stocks.map((stock) => (
          <StockCard key={stock.ticker} stock={stock} />
        ))}
      </div>
    </section>
  );
}
