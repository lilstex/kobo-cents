"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { StatusTag } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";

type FavoriteItem = components["schemas"]["FavoriteItem"];

/** The watching/owned tag is its own tap target, per docs/
 * frontend-architecture/06-design.md: an outlined tag versus a filled
 * one, readable at a glance, and switching it is a single toggle, no
 * form, matching 01_product.md's "a tag, not a transaction log." A
 * sibling of the ticker link, not nested inside it, an interactive
 * element inside an anchor isn't valid HTML. */
export function FavoriteRow({
  favorite,
  onToggleStatus,
  onRemove,
}: {
  favorite: FavoriteItem;
  onToggleStatus: (stockId: string, next: "watching" | "owned") => void;
  onRemove: (stockId: string) => void;
}) {
  const up = isUp(favorite.change_percent);
  return (
    <div className="flex items-center justify-between border-b border-border py-2.5">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Link href={`/app/stocks/${favorite.ticker}`} className="text-sm font-bold text-text">
            {favorite.ticker}
          </Link>
          <button
            type="button"
            onClick={() =>
              onToggleStatus(favorite.stock_id, favorite.status === "watching" ? "owned" : "watching")
            }
          >
            <StatusTag status={favorite.status as "watching" | "owned"} />
          </button>
        </div>
        <div className="mt-0.5 truncate text-[11.5px] text-muted">{favorite.company_name}</div>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <div className="text-right">
          <div className="font-mono text-[13.5px] font-semibold text-text">
            {formatPrice(favorite.price, favorite.market as "NG" | "US")}
          </div>
          <div className={`font-mono text-[11.5px] font-semibold ${up ? "text-brand" : "text-down"}`}>
            {formatChangePercent(favorite.change_percent)}
          </div>
        </div>
        <button
          type="button"
          onClick={() => onRemove(favorite.stock_id)}
          aria-label={`Remove ${favorite.ticker} from favorites`}
          className="text-muted hover:text-down"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
