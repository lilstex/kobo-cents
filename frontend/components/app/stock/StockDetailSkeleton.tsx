import { Skeleton } from "@/components/ui";

/** Shaped like the real price block, chart area, and metric cards,
 * per docs/frontend-architecture/05-app-plan.md's never-a-spinner
 * rule, the same as Phase 4's MarketOverviewSkeleton. */
export function StockDetailSkeleton() {
  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <Skeleton className="mb-1.5 h-4 w-20" />
      <Skeleton className="mb-1 h-8 w-32" />
      <Skeleton className="mb-4 h-4 w-40" />
      <Skeleton className="mb-6 h-40 w-full" />
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="mb-2.5 h-20 w-full" />
      ))}
    </div>
  );
}
