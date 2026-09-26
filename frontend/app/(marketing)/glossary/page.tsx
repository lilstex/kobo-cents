import type { Metadata } from "next";
import Link from "next/link";
import { GLOSSARY_CATEGORIES, getAllGlossaryTerms, getGlossaryTermsByCategory } from "@/lib/glossary";
import { definedTermSetSchema } from "@/lib/structured-data";

export const metadata: Metadata = {
  title: "Stock research glossary — Kobo & Cents",
  description:
    "Plain-language definitions for every metric Kobo & Cents uses to research Nigerian and US stocks, liquidity, equity, profitability, valuation, and dividends.",
};

export default function GlossaryIndexPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-16 sm:py-20">
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(definedTermSetSchema(getAllGlossaryTerms())),
        }}
      />
      <h1 className="mb-3 text-3xl font-extrabold text-text">Glossary</h1>
      <p className="mb-12 max-w-xl text-sm leading-relaxed text-muted">
        Every metric shown on a Kobo &amp; Cents stock page, explained in
        plain language, the same explanations used inline throughout the
        product itself.
      </p>

      <div className="flex flex-col gap-12">
        {GLOSSARY_CATEGORIES.map(({ key, label }) => {
          const terms = getGlossaryTermsByCategory(key);
          if (terms.length === 0) return null;
          return (
            <section key={key}>
              <h2 className="mb-4 font-mono text-xs font-semibold uppercase tracking-widest text-brand">
                {label}
              </h2>
              <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
                {terms.map((term) => (
                  <li key={term.slug}>
                    <Link
                      href={`/glossary/${term.slug}`}
                      className="block px-4 py-3 hover:bg-surface"
                    >
                      <span className="text-sm font-semibold text-text">{term.term}</span>
                      <p className="mt-1 text-xs leading-relaxed text-muted">
                        {term.shortDefinition}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </main>
  );
}
