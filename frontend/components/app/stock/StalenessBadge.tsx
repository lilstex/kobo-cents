import { Clock } from "lucide-react";

// docs/backend-architecture/02.md's per-stock last_successful_refresh_at
// is exactly what this reads, per docs/frontend-architecture/
// 05-app-plan.md: "data as of [time]," not an error banner and not
// silently pretending the data is current. There's no market-wide
// "the current cycle finished at this timestamp" endpoint to compare
// against yet (a real, tracked simplification, see docs/open-items.md),
// so this uses a fixed age window instead: refreshes run two to three
// times a day per 01_product.md, so data past roughly one and a half
// cycles old is a reasonable proxy for "the current cycle hasn't
// caught up with this stock yet."
const STALE_THRESHOLD_HOURS = 18;

export function StalenessBadge({ asOf }: { asOf: string | null }) {
  if (!asOf) return null;
  const ageHours = (Date.now() - new Date(asOf).getTime()) / (1000 * 60 * 60);
  if (ageHours < STALE_THRESHOLD_HOURS) return null;

  const formatted = new Date(asOf).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1.5 font-mono text-[11px] font-medium text-muted">
      <Clock className="h-3 w-3" />
      Data as of {formatted}, today&apos;s refresh is still catching up on this stock
    </div>
  );
}
