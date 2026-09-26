import type { MetadataRoute } from "next";
import { getAllGlossaryTerms } from "@/lib/glossary";

const SITE_URL = "https://koboandcents.com";

// The exact same term list that drives generateStaticParams for the
// glossary pages themselves, per docs/frontend-architecture/
// 04-landing-page-indepth.md, one list, no separate list to remember
// to keep in sync. /terms and /privacy exist and are crawlable (see
// robots.ts) but stay out of this file on purpose, they're not
// content worth ranking for.
export default function sitemap(): MetadataRoute.Sitemap {
  const terms = getAllGlossaryTerms();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "weekly", priority: 1.0 },
    { url: `${SITE_URL}/glossary`, changeFrequency: "monthly", priority: 0.8 },
  ];

  const termRoutes: MetadataRoute.Sitemap = terms.map((term) => ({
    url: `${SITE_URL}/glossary/${term.slug}`,
    changeFrequency: "yearly",
    priority: 0.6,
  }));

  return [...staticRoutes, ...termRoutes];
}
