"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CompareStack } from "@/components/app/compare/CompareStack";
import { CompareTable } from "@/components/app/compare/CompareTable";
import { TickerPicker } from "@/components/app/compare/TickerPicker";
import { FormError } from "@/components/auth/FormError";
import { Skeleton } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

type CompareResponse = components["schemas"]["CompareResponse"];

function tickersFromParam(value: string | null): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((t) => t.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 3);
}

// useSearchParams needs a Suspense boundary (see app/app/compare/
// page.tsx), the same reason MarketOverview and StockDetailView are
// split from their page.tsx files.
export function CompareView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlTickers = tickersFromParam(searchParams.get("tickers"));

  const [pickerTickers, setPickerTickers] = useState<string[]>(urlTickers);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (urlTickers.length < 2) {
      setResult(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      const { data, error: apiError, response } = await apiClient.GET("/api/v1/compare", {
        params: { query: { tickers: urlTickers.join(",") } },
      });
      if (cancelled) return;
      setLoading(false);

      if (response.status === 401) {
        router.push("/");
        return;
      }
      if (apiError) {
        setError(extractErrorMessage(apiError, "Could not compare these stocks."));
        setResult(null);
        return;
      }
      setResult(data ?? null);
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get("tickers"), router]);

  function handleCompare() {
    router.push(`/app/compare?tickers=${pickerTickers.join(",")}`);
  }

  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <h1 className="mb-4 text-lg font-bold text-text">Compare</h1>

      <TickerPicker selected={pickerTickers} onChange={setPickerTickers} onCompare={handleCompare} />

      {error ? <FormError message={error} /> : null}

      {loading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : null}

      {!loading && !error && result ? (
        <div className="overflow-x-auto">
          <CompareTable stocks={result.stocks} bestInComparison={result.best_in_comparison} />
          <CompareStack stocks={result.stocks} bestInComparison={result.best_in_comparison} />
        </div>
      ) : null}
    </div>
  );
}
