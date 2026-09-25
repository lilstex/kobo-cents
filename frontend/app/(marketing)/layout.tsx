import { Footer } from "@/components/marketing/Footer";
import { Header } from "@/components/marketing/Header";
import { MobileStickyCta } from "@/components/marketing/MobileStickyCta";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      {/* Bottom padding reserved on mobile only, matching the sticky
       * bar's own height, so it never covers the final CTA section's
       * own button underneath it. */}
      <div className="pb-20 sm:pb-0">{children}</div>
      <Footer />
      <MobileStickyCta />
    </>
  );
}
