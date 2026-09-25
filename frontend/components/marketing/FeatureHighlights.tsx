import { Zap } from "lucide-react";
import { BucketChip, Card, StatusTag } from "@/components/ui";

/** Benefit-first headlines, not feature-first ones, per
 * docs/frontend-architecture/03-landing-page.md: "know why, not just
 * what" rather than "explainability panel." Each visual is a real
 * fragment of the actual component it's describing, built in
 * Sub-phase 0.2, not an illustration standing in for it. */
export function FeatureHighlights() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
        <h2 className="mb-10 text-2xl font-bold text-text sm:text-3xl">
          Everything you need, none of what you don&apos;t
        </h2>
        <div className="grid gap-6 sm:grid-cols-2">
          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-lg font-semibold text-text">
              Know where a stock stands, at a glance
            </h3>
            <p className="text-sm leading-relaxed text-muted">
              Every stock sorted into one of three buckets, ranked against
              its own sector, not the whole market.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <BucketChip variant="well" />
              <BucketChip variant="potential" />
              <BucketChip variant="under" />
            </div>
          </Card>

          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-lg font-semibold text-text">Know why, not just what</h3>
            <p className="text-sm leading-relaxed text-muted">
              An actual explanation for every bucket, in plain language, not
              a data dump.
            </p>
            <div className="mt-2 flex items-start gap-2 rounded-lg border border-border bg-bg p-3">
              <Zap className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden="true" />
              <p className="text-xs leading-relaxed text-text">
                &ldquo;ROE is strong and trending up, but revenue growth has
                slowed the last two quarters, that combination is why this
                is a watch, not a clear buy.&rdquo;
              </p>
            </div>
          </Card>

          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-lg font-semibold text-text">
              Put two or three stocks side by side
            </h3>
            <p className="text-sm leading-relaxed text-muted">
              The same metrics, the same order, a straight read across a
              row instead of flipping between tabs.
            </p>
            <div className="mt-2 flex flex-col gap-1.5 font-mono text-xs text-muted">
              <div className="flex justify-between border-b border-border pb-1.5">
                <span>Return on Equity</span>
                <span className="text-text">24.6% &middot; 18.1% &middot; 14.9%</span>
              </div>
              <div className="flex justify-between">
                <span>Dividend yield</span>
                <span className="text-text">4.1% &middot; 5.6% &middot; 3.0%</span>
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-4 p-6">
            <h3 className="text-lg font-semibold text-text">
              Track what you&apos;re watching, and what you own
            </h3>
            <p className="text-sm leading-relaxed text-muted">
              A clear tag for a stock you&apos;re keeping an eye on versus
              one you already hold, visible at a glance in your list.
            </p>
            <div className="mt-2 flex gap-2">
              <StatusTag status="watching" />
              <StatusTag status="owned" />
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
