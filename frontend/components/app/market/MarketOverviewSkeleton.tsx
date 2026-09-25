import { Skeleton } from "@/components/ui";

/** Shaped like the real pill toggle, sector chips, and stock rows,
 * per docs/frontend-architecture/05-app-plan.md's never-a-spinner
 * rule, shown while the first fetch for a market/sector combination
 * is in flight. */
export function MarketOverviewSkeleton() {
  return (
    <div>
      <Skeleton className="mb-3.5 h-9 rounded-full" />
      <div className="mb-2 flex gap-2">
        <Skeleton className="h-7 w-20 shrink-0 rounded-full" />
        <Skeleton className="h-7 w-28 shrink-0 rounded-full" />
        <Skeleton className="h-7 w-24 shrink-0 rounded-full" />
      </div>
      <Skeleton className="mb-3 mt-4 h-5 w-32" />
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center justify-between border-b border-border py-2.5">
          <div>
            <Skeleton className="mb-1.5 h-3.5 w-16" />
            <Skeleton className="h-2.5 w-28" />
          </div>
          <Skeleton className="h-3.5 w-14" />
        </div>
      ))}
    </div>
  );
}
