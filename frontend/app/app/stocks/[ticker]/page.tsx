import { MDXRemote } from "next-mdx-remote/rsc";
import type { Metadata } from "next";
import { StockDetailView } from "@/components/app/stock/StockDetailView";
import { getAllGlossaryTerms } from "@/lib/glossary";

// Next.js 16: dynamic route params are a Promise, not a plain object,
// the same breaking change already hit once on the glossary pages.
type Params = Promise<{ ticker: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { ticker } = await params;
  return { title: `${ticker.toUpperCase()} — Kobo & Cents` };
}

// An async Server Component specifically so the glossary drawer (Sub-
// phase 5.3) can use the exact same MDX source the public /glossary
// pages render from: next-mdx-remote/rsc's <MDXRemote> only ever
// renders on the server, never in a client component. All 11 terms
// (a small, fixed set) are pre-rendered here once and handed down as
// already-rendered React nodes to the interactive, client-side
// StockDetailView, which does the actual data fetching and decides
// which one to reveal.
export default async function StockDetailPage({ params }: { params: Params }) {
  const { ticker } = await params;
  const terms = getAllGlossaryTerms();
  const glossaryContent = Object.fromEntries(
    terms.map((term) => [term.slug, <MDXRemote key={term.slug} source={term.body} />]),
  );

  return <StockDetailView ticker={ticker.toUpperCase()} glossaryContent={glossaryContent} />;
}
