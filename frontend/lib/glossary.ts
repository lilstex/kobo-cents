import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

export type GlossaryCategory =
  | "liquidity"
  | "equity"
  | "profitability"
  | "valuation-and-growth"
  | "dividends";

export type GlossaryTerm = {
  slug: string;
  term: string;
  category: GlossaryCategory;
  shortDefinition: string;
  body: string;
};

export const GLOSSARY_CATEGORIES: { key: GlossaryCategory; label: string }[] = [
  { key: "liquidity", label: "Liquidity" },
  { key: "equity", label: "Equity" },
  { key: "profitability", label: "Profitability" },
  { key: "valuation-and-growth", label: "Valuation and Growth" },
  { key: "dividends", label: "Dividends" },
];

const GLOSSARY_DIR = path.join(process.cwd(), "content", "glossary");

/**
 * The single source feeding the glossary index, generateStaticParams,
 * and the sitemap, per docs/frontend-architecture/04-landing-page-
 * indepth.md: one list of terms driving all three, so they can never
 * silently drift out of sync with each other.
 */
export function getAllGlossaryTerms(): GlossaryTerm[] {
  const files = fs.readdirSync(GLOSSARY_DIR).filter((file) => file.endsWith(".mdx"));

  const terms = files.map((file) => {
    const raw = fs.readFileSync(path.join(GLOSSARY_DIR, file), "utf-8");
    const { data, content } = matter(raw);
    return {
      slug: data.slug as string,
      term: data.term as string,
      category: data.category as GlossaryCategory,
      shortDefinition: data.shortDefinition as string,
      body: content,
    };
  });

  return terms.sort((a, b) => a.term.localeCompare(b.term));
}

export function getGlossaryTermBySlug(slug: string): GlossaryTerm | undefined {
  return getAllGlossaryTerms().find((term) => term.slug === slug);
}

export function getGlossaryTermsByCategory(category: GlossaryCategory): GlossaryTerm[] {
  return getAllGlossaryTerms().filter((term) => term.category === category);
}
