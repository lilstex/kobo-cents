import { Check, X } from "lucide-react";

const DOES = [
  "Shows liquidity, profitability, valuation, and dividend metrics in plain language",
  "Tells you why a stock landed in its bucket, not just that it did",
  "Covers Nigerian and US stocks, always as two separate views",
  "Refreshes two to three times a day, and always shows when",
];

const NEVER = [
  "Places an order on your behalf",
  "Holds or moves your money",
  "Executes anything, ever, at any stage",
  "Mixes Nigerian and US stocks into one list",
];

/** High on the page, not buried in an FAQ, per
 * docs/frontend-architecture/03-landing-page.md: "is this a trading
 * app" is the confusion this category invites, answered before it's
 * asked. */
export function TrustSection() {
  return (
    <section id="trust" className="border-t border-border bg-surface/40">
      <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
        <h2 className="mb-10 text-2xl font-bold text-text sm:text-3xl">
          What Kobo &amp; Cents is, and isn&apos;t
        </h2>
        <div className="grid gap-8 sm:grid-cols-2">
          <div className="flex flex-col gap-4">
            <h3 className="font-mono text-xs font-semibold uppercase tracking-widest text-brand">
              What it does
            </h3>
            <ul className="flex flex-col gap-3">
              {DOES.map((item) => (
                <li key={item} className="flex gap-3 text-sm text-text">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col gap-4">
            <h3 className="font-mono text-xs font-semibold uppercase tracking-widest text-down">
              What it never does
            </h3>
            <ul className="flex flex-col gap-3">
              {NEVER.map((item) => (
                <li key={item} className="flex gap-3 text-sm text-text">
                  <X className="mt-0.5 h-4 w-4 shrink-0 text-down" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
