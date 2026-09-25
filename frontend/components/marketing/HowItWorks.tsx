const STEPS = [
  {
    title: "Create a free account",
    description: "Email and password, nothing else asked for upfront.",
  },
  {
    title: "Pick Nigerian or US stocks",
    description:
      "Nigeria first, by default, every time you log in. Switch to US stocks whenever you want, the two markets never blend into one list.",
  },
  {
    title: "See why, not just what",
    description:
      "Every stock lands in performing well, showing potential, or underperforming, with the actual reasoning behind it, not just a label.",
  },
  {
    title: "Compare, favorite, or move on",
    description:
      "Watch a stock, mark one you already own, or line two or three up side by side, whatever the moment actually calls for.",
  },
];

/** A real sequence, numbered because it genuinely is one, per
 * docs/frontend-architecture/03-landing-page.md. */
export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
      <h2 className="mb-10 text-2xl font-bold text-text sm:text-3xl">How it works</h2>
      <ol className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step, i) => (
          <li key={step.title} className="flex flex-col gap-2">
            <span className="font-mono text-2xl font-bold text-brand">
              {String(i + 1).padStart(2, "0")}
            </span>
            <h3 className="text-base font-semibold text-text">{step.title}</h3>
            <p className="text-sm leading-relaxed text-muted">{step.description}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
