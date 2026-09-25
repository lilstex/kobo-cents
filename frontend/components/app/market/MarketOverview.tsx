"use client";

import { Search } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { BucketSection } from "@/components/app/market/BucketSection";
import { MarketOverviewSkeleton } from "@/components/app/market/MarketOverviewSkeleton";
import { MarketToggle } from "@/components/app/market/MarketToggle";
import { SectorChips } from "@/components/app/market/SectorChips";
import { FormError } from "@/components/auth/FormError";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { type Market, sectorsForMarket } from "@/lib/sectors";

type StockSummary = components["schemas"]["StockSummary"];
type BucketKey = "well" | "potential" | "under";
const BUCKETS: BucketKey[] = ["well", "potential", "under"];

type BucketData = { total: number; items: StockSummary[] };

// The market overview reads already-scored rows the refresh job
// computed, per docs/backend-architecture/01.md, so this page never
// runs any scoring itself, it fetches each bucket in parallel and
// renders what comes back. useSearchParams needs a Suspense boundary
// (see app/app/page.tsx), the same reason VerifyStatus and
// ResetPasswordForm are split from their page.tsx files.
export function MarketOverview() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const market = (searchParams.get("market") === "us" ? "us" : "ng") as Market;
  const sector = searchParams.get("sector");

  const [buckets, setBuckets] = useState<Record<BucketKey, BucketData> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setBuckets(null);
    setError(null);

    async function load() {
      const results = await Promise.all(
        BUCKETS.map((bucket) =>
          apiClient.GET("/api/v1/markets/{market}/overview", {
            params: {
              path: { market: market.toUpperCase() },
              query: { bucket, sector: sector ?? undefined, limit: 20 },
            },
          }),
        ),
      );
      if (cancelled) return;

      const unauthorized = results.some((r) => r.response.status === 401);
      if (unauthorized) {
        router.push("/");
        return;
      }

      const failed = results.find((r) => r.error);
      if (failed) {
        setError(extractErrorMessage(failed.error, "Could not load the market overview."));
        return;
      }

      const next = {} as Record<BucketKey, BucketData>;
      BUCKETS.forEach((bucket, i) => {
        const data = results[i].data;
        next[bucket] = { total: data?.total ?? 0, items: data?.items ?? [] };
      });
      setBuckets(next);
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [market, sector, router]);

  function setMarket(next: Market) {
    const params = new URLSearchParams();
    if (next !== "ng") params.set("market", next);
    router.push(params.toString() ? `/app?${params.toString()}` : "/app");
  }

  function setSector(next: string | null) {
    const params = new URLSearchParams();
    if (market !== "ng") params.set("market", market);
    if (next) params.set("sector", next);
    router.push(params.toString() ? `/app?${params.toString()}` : "/app");
  }

  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-bold text-text">Markets</h1>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-text">
          <Search className="h-4 w-4" />
        </div>
      </div>

      <MarketToggle market={market} onChange={setMarket} className="mb-3.5 max-w-xs" />
      <SectorChips sectors={sectorsForMarket(market)} selected={sector} onSelect={setSector} />

      {error ? <FormError message={error} /> : null}

      {!error && !buckets ? <MarketOverviewSkeleton /> : null}

      {!error && buckets ? (
        BUCKETS.every((bucket) => buckets[bucket].total === 0) ? (
          <p className="py-12 text-center text-sm text-muted">
            No stocks in this market{sector ? " for this sector" : ""} yet.
          </p>
        ) : (
          BUCKETS.map((bucket) => (
            <BucketSection
              key={bucket}
              bucket={bucket}
              total={buckets[bucket].total}
              stocks={buckets[bucket].items}
            />
          ))
        )
      ) : null}
    </div>
  );
}
