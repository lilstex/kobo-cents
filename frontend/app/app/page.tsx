import type { Metadata } from "next";
import { Suspense } from "react";
import { MarketOverview } from "@/components/app/market/MarketOverview";
import { MarketOverviewSkeleton } from "@/components/app/market/MarketOverviewSkeleton";

export const metadata: Metadata = { title: "Markets — Kobo & Cents" };

export default function AppHomePage() {
  return (
    <Suspense
      fallback={
        <div className="px-4 pt-4 sm:px-6 sm:pt-6">
          <MarketOverviewSkeleton />
        </div>
      }
    >
      <MarketOverview />
    </Suspense>
  );
}
