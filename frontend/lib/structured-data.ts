import type { GlossaryTerm } from "./glossary";

const SITE_URL = "https://koboandcents.com";

/**
 * Typed JSON-LD builders, per docs/frontend-architecture/
 * 04-landing-page-indepth.md: generated, never a hand-typed JSON
 * string scattered across a page file where a stray comma silently
 * breaks structured data with no visible error.
 */

export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Kobo & Cents",
    url: SITE_URL,
    logo: `${SITE_URL}/logo-512.png`,
    parentOrganization: {
      "@type": "Organization",
      name: "ShotNub Solutions",
    },
  };
}

export function softwareApplicationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Kobo & Cents",
    applicationCategory: "FinanceApplication",
    operatingSystem: "Web",
    description:
      "Nigerian and US stock research. Understand a stock before you decide anything about it. Never a trading platform.",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };
}

export function definedTermSetSchema(terms: GlossaryTerm[]) {
  return {
    "@context": "https://schema.org",
    "@type": "DefinedTermSet",
    name: "Kobo & Cents stock research glossary",
    url: `${SITE_URL}/glossary`,
    hasDefinedTerm: terms.map((term) => definedTermSchema(term, { bare: true })),
  };
}

export function definedTermSchema(term: GlossaryTerm, options?: { bare?: boolean }) {
  const schema = {
    "@type": "DefinedTerm" as const,
    name: term.term,
    description: term.shortDefinition,
    inDefinedTermSet: `${SITE_URL}/glossary`,
    url: `${SITE_URL}/glossary/${term.slug}`,
  };
  if (options?.bare) return schema;
  return { "@context": "https://schema.org", ...schema };
}
