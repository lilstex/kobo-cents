"use client";

import { ArrowLeft, Star } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ExplainabilityPanel } from "@/components/app/stock/ExplainabilityPanel";
import { GlossaryDrawer } from "@/components/app/stock/GlossaryDrawer";
import { GlossarySheet } from "@/components/app/stock/GlossarySheet";
import { MetricCard } from "@/components/app/stock/MetricCard";
import { PriceChart } from "@/components/app/stock/PriceChart";
import { StalenessBadge } from "@/components/app/stock/StalenessBadge";
import { StockDetailSkeleton } from "@/components/app/stock/StockDetailSkeleton";
import { FormError } from "@/components/auth/FormError";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { markEngagementMilestone } from "@/lib/installMilestone";
import { formatChangePercent, formatPrice, isUp } from "@/lib/marketFormat";

type StockDetailResponse = components["schemas"]["StockDetailResponse"];
type PricePoint = components["schemas"]["PricePoint"];
type FavoriteItem = components["schemas"]["FavoriteItem"];

export function StockDetailView({
  ticker,
  glossaryContent,
}: {
  ticker: string;
  glossaryContent: Record<string, ReactNode>;
}) {
  const router = useRouter();
  const [detail, setDetail] = useState<StockDetailResponse | null>(null);
  const [prices, setPrices] = useState<PricePoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [openMetricKey, setOpenMetricKey] = useState<string | null>(null);
  const [openDrawer, setOpenDrawer] = useState<{ slug: string; term: string } | null>(null);
  const [favorite, setFavorite] = useState<FavoriteItem | null>(null);
  const [favoriteBusy, setFavoriteBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setError(null);

    async function load() {
      const [detailResult, historyResult, favoritesResult] = await Promise.all([
        apiClient.GET("/api/v1/stocks/{ticker}", { params: { path: { ticker } } }),
        apiClient.GET("/api/v1/stocks/{ticker}/price-history", { params: { path: { ticker } } }),
        apiClient.GET("/api/v1/favorites"),
      ]);
      if (cancelled) return;

      if (detailResult.response.status === 401) {
        router.push("/");
        return;
      }
      if (detailResult.error) {
        setError(extractErrorMessage(detailResult.error, "Could not load this stock."));
        return;
      }
      setDetail(detailResult.data ?? null);
      setPrices(historyResult.data?.items ?? []);
      setFavorite(
        favoritesResult.data?.items.find((item) => item.ticker === ticker.toUpperCase()) ?? null,
      );
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [ticker, router]);

  async function handleToggleFavorite() {
    if (!detail || favoriteBusy) return;
    setFavoriteBusy(true);
    if (favorite) {
      const { response } = await apiClient.DELETE("/api/v1/favorites/{stock_id}", {
        params: { path: { stock_id: favorite.stock_id } },
      });
      if (response.status === 204) setFavorite(null);
    } else {
      const { data } = await apiClient.POST("/api/v1/favorites", {
        body: { ticker: detail.ticker, market: detail.market },
      });
      if (data) {
        setFavorite(data);
        // The install prompt's engagement milestone, per docs/
        // frontend-architecture/05-app-plan.md's Sub-phase 3.4: no
        // caller existed until Favorites (Phase 7) gave it a real
        // "first favorite added" moment to fire on.
        markEngagementMilestone();
      }
    }
    setFavoriteBusy(false);
  }

  if (error) {
    return (
      <div className="px-4 pt-4 sm:px-6 sm:pt-6">
        <FormError message={error} />
      </div>
    );
  }

  if (!detail) return <StockDetailSkeleton />;

  const up = isUp(detail.change_percent);
  const oldestAsOf = [detail.scores_as_of, detail.price_as_of, detail.fundamentals_as_of]
    .filter((value): value is string => value !== null)
    .sort()[0];
  const openMetric = openMetricKey ? detail.glossary[openMetricKey] : null;

  return (
    <div className="px-4 pt-4 sm:px-6 sm:pt-6">
      <div className="mb-3 flex items-center justify-between">
        <Link href="/app" className="flex items-center text-muted hover:text-text">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <button
          type="button"
          onClick={handleToggleFavorite}
          disabled={favoriteBusy}
          aria-label={favorite ? "Remove from favorites" : "Add to favorites"}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface text-text disabled:opacity-50"
        >
          <Star
            className={`h-4 w-4 ${favorite ? "fill-brand text-brand" : ""}`}
          />
        </button>
      </div>

      <div className="mb-1">
        <div className="text-lg font-bold text-text">{detail.ticker}</div>
        <div className="text-xs text-muted">{detail.company_name}</div>
      </div>

      <div className="mb-2 pt-1">
        <div className="font-mono text-[28px] font-extrabold text-text">
          {formatPrice(detail.price, detail.market as "NG" | "US")}
        </div>
        <div className={`font-mono text-[13px] font-bold ${up ? "text-brand" : "text-down"}`}>
          {formatChangePercent(detail.change_percent)} today
        </div>
      </div>

      <StalenessBadge asOf={oldestAsOf ?? null} />

      <div className="mb-4">
        <PriceChart points={prices} />
      </div>

      <ExplainabilityPanel bucket={detail.bucket} explanation={detail.explanation} />

      {detail.categories.map((category) => (
        <MetricCard
          key={category.category}
          category={category}
          glossary={detail.glossary}
          onSelectMetric={setOpenMetricKey}
        />
      ))}

      {openMetric ? (
        <GlossarySheet
          term={openMetric.term}
          shortDefinition={openMetric.short_definition}
          onClose={() => setOpenMetricKey(null)}
          onOpenFullEntry={() => {
            setOpenDrawer({ slug: openMetric.slug, term: openMetric.term });
            setOpenMetricKey(null);
          }}
        />
      ) : null}

      {openDrawer ? (
        <GlossaryDrawer
          term={openDrawer.term}
          content={glossaryContent[openDrawer.slug]}
          onClose={() => setOpenDrawer(null)}
        />
      ) : null}
    </div>
  );
}
