import { LineChart } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

// Next.js 16: dynamic route params are a Promise, not a plain object,
// the same breaking change already hit once on the glossary pages.
type Params = Promise<{ ticker: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { ticker } = await params;
  return { title: `${ticker.toUpperCase()} — Kobo & Cents` };
}

// Market overview stock rows and cards (Phase 4) already link here;
// the real screen, price chart, metric cards, explainability panel,
// glossary popover, is Phase 5 work and doesn't exist yet, this
// placeholder exists so that link lands somewhere real today instead
// of a generic 404.
export default async function StockDetailPage({ params }: { params: Params }) {
  const { ticker } = await params;
  return (
    <EmptyState
      icon={LineChart}
      title={`${ticker.toUpperCase()}'s detail page is next`}
      description="Price chart, metric categories, and the explainability panel are landing here soon."
    />
  );
}
