"use client";

import { Heart, Share2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FavoriteRow } from "@/components/app/favorites/FavoriteRow";
import { ShareModal } from "@/components/app/favorites/ShareModal";
import { PaywallSheet } from "@/components/app/PaywallSheet";
import { FormError } from "@/components/auth/FormError";
import { EmptyState, LinkButton, Skeleton } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

type FavoriteItem = components["schemas"]["FavoriteItem"];

export function FavoritesView() {
  const router = useRouter();
  const [items, setItems] = useState<FavoriteItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sharingEntitled, setSharingEntitled] = useState<boolean | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { data, error: apiError, response } = await apiClient.GET("/api/v1/favorites");
      if (cancelled) return;
      if (response.status === 401) {
        router.push("/");
        return;
      }
      if (apiError) {
        setError(extractErrorMessage(apiError, "Could not load your favorites."));
        return;
      }
      setItems(data?.items ?? []);

      const entitlementResult = await apiClient.GET("/api/v1/subscriptions/entitlement", {
        params: { query: { feature: "sharing" } },
      });
      if (cancelled) return;
      setSharingEntitled(entitlementResult.data?.entitled ?? false);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [router]);

  function handleShareClick() {
    if (sharingEntitled) {
      setShowShareModal(true);
    } else {
      setShowPaywall(true);
    }
  }

  async function handleToggleStatus(stockId: string, next: "watching" | "owned") {
    const { data, error: apiError } = await apiClient.PATCH("/api/v1/favorites/{stock_id}", {
      params: { path: { stock_id: stockId } },
      body: { status: next },
    });
    if (apiError || !data) return;
    setItems((current) =>
      (current ?? []).map((item) => (item.stock_id === stockId ? data : item)),
    );
  }

  async function handleRemove(stockId: string) {
    const { response } = await apiClient.DELETE("/api/v1/favorites/{stock_id}", {
      params: { path: { stock_id: stockId } },
    });
    if (response.status !== 204) return;
    setItems((current) => (current ?? []).filter((item) => item.stock_id !== stockId));
  }

  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-bold text-text">Favorites</h1>
        {!error && items && items.length > 0 ? (
          <button
            type="button"
            onClick={handleShareClick}
            className="flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-brand"
          >
            <Share2 className="h-3.5 w-3.5" />
            Share
          </button>
        ) : null}
      </div>

      {error ? <FormError message={error} /> : null}

      {!error && !items ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex items-center justify-between py-2.5">
              <div>
                <Skeleton className="mb-1.5 h-3.5 w-16" />
                <Skeleton className="h-2.5 w-28" />
              </div>
              <Skeleton className="h-3.5 w-14" />
            </div>
          ))}
        </div>
      ) : null}

      {!error && items && items.length === 0 ? (
        <EmptyState
          icon={Heart}
          title="Nothing saved yet"
          description="Add a stock from the market overview to watch it here, or mark one you already own."
          action={<LinkButton href="/app">Browse the market</LinkButton>}
        />
      ) : null}

      {!error && items && items.length > 0 ? (
        <div>
          {items.map((item) => (
            <FavoriteRow
              key={item.stock_id}
              favorite={item}
              onToggleStatus={handleToggleStatus}
              onRemove={handleRemove}
            />
          ))}
        </div>
      ) : null}

      {showPaywall ? <PaywallSheet onClose={() => setShowPaywall(false)} /> : null}
      {showShareModal ? <ShareModal onClose={() => setShowShareModal(false)} /> : null}
    </div>
  );
}
