/** Honest Stage-0 credibility, per docs/frontend-architecture/
 * 03-landing-page.md: no fabricated testimonials or user counts,
 * transparency about the data instead, and a real first-person note. */
export function Credibility() {
  return (
    <section className="mx-auto max-w-3xl px-6 py-16 sm:py-20">
      <div className="rounded-lg border border-border bg-surface p-6 sm:p-8">
        <p className="mb-6 font-mono text-xs text-muted">
          Data refreshes two to three times a day, not real-time, every page
          shows exactly when it last updated. This is a research tool, not
          a trading terminal, and it's built for that on purpose.
        </p>
        <p className="text-sm leading-relaxed text-text">
          I built Kobo &amp; Cents because I kept doing the same thing
          myself: checking a stock's numbers on one site, its news on
          another, and trying to work out what any of it actually meant
          without a background in finance to fall back on. Nigerian stock
          research especially felt like it was missing a place that just
          explained the numbers, plainly, before asking anyone to act on
          them. This is that place, built first for Nigeria, US stocks
          alongside it, and it will stay a research tool, never a trading
          one.
        </p>
      </div>
    </section>
  );
}
