import type { Metadata } from "next";
import { Credibility } from "@/components/marketing/Credibility";
import { FeatureHighlights } from "@/components/marketing/FeatureHighlights";
import { FinalCta } from "@/components/marketing/FinalCta";
import { Hero } from "@/components/marketing/Hero";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { TrustSection } from "@/components/marketing/TrustSection";
import { TwoMarkets } from "@/components/marketing/TwoMarkets";

export const metadata: Metadata = {
  title: "Kobo & Cents — Nigerian and US stock research",
  description:
    "Understand a stock before you decide anything about it. Plain-language Nigerian and US stock research, never a trading platform.",
};

// Fully static: no per-request data fetch anywhere on this page, per
// docs/frontend-architecture/04-landing-page-indepth.md. Every section
// below is server-rendered once at build time.
export default function LandingPage() {
  return (
    <main>
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
