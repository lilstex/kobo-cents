import { StatusTag } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";

type ShareSnapshotItem = components["schemas"]["ShareSnapshotItem"];

/** Read-only, per docs/backend-architecture/02.md: "here's what I'm
 * watching right now," a frozen snapshot, not a live view someone
 * else's account keeps drifting underneath. No links back into
 * `/app`, the viewer here may have no session at all. */
export function SharedFavoritesList({
  items,
  createdAt,
}: {
  items: ShareSnapshotItem[];
  createdAt: string;
}) {
  const createdLabel = new Date(createdAt).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <div>
      <p className="mb-5 text-xs text-muted">Snapshot taken {createdLabel}.</p>
      {items.length === 0 ? (
        <p className="text-sm text-muted">This list was empty when it was shared.</p>
      ) : (
        <div>
          {items.map((item) => {
            const up = isUp(item.change_percent);
            return (
              <div
                key={item.ticker}
                className="flex items-center justify-between border-b border-border py-2.5"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-text">{item.ticker}</span>
                    <StatusTag status={item.status as "watching" | "owned"} />
                  </div>
                  <div className="mt-0.5 truncate text-[11.5px] text-muted">
                    {item.company_name}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <div className="text-right">
                    <div className="font-mono text-[13.5px] font-semibold text-text">
                      {formatPrice(item.price, item.market as "NG" | "US")}
                    </div>
                    <div
                      className={`font-mono text-[11.5px] font-semibold ${up ? "text-brand" : "text-down"}`}
                    >
                      {formatChangePercent(item.change_percent)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
