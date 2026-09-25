import type { Metadata } from "next";
import { Credibility } from "@/components/marketing/Credibility";
import { FeatureHighlights } from "@/components/marketing/FeatureHighlights";
import { FinalCta } from "@/components/marketing/FinalCta";
import { Hero } from "@/components/marketing/Hero";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { TrustSection } from "@/components/marketing/TrustSection";
import { TwoMarkets } from "@/components/marketing/TwoMarkets";
import { softwareApplicationSchema } from "@/lib/structured-data";

const TITLE = "Kobo & Cents — Nigerian and US stock research";
const DESCRIPTION =
  "Understand a stock before you decide anything about it. Plain-language Nigerian and US stock research, never a trading platform.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    images: [{ url: "/og-landing.png", width: 1200, height: 630 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: ["/og-landing.png"],
  },
};

// Fully static: no per-request data fetch anywhere on this page, per
// docs/frontend-architecture/04-landing-page-indepth.md. Every section
// below is server-rendered once at build time.
export default function LandingPage() {
  return (
    <main>
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApplicationSchema()) }}
      />
      <Hero />
      <TrustSection />
      <HowItWorks />
      <FeatureHighlights />
      <TwoMarkets />
      <Credibility />
      <FinalCta />
    </main>
  );
}
