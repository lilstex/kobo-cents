import Link from "next/link";
import { LinkButton } from "@/components/ui";
import { HeroVisual } from "./HeroVisual";

export function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-10 px-6 py-16 sm:py-24 lg:grid-cols-2 lg:gap-6">
      <div className="flex flex-col gap-6">
        <p className="font-mono text-xs font-semibold uppercase tracking-widest text-brand">
          Stock research &middot; NG + US
        </p>
        <h1 className="text-3xl font-extrabold leading-tight text-text sm:text-4xl lg:text-5xl">
          Understand a stock before you decide anything about it.
        </h1>
        <p className="max-w-xl text-base leading-relaxed text-muted sm:text-lg">
          Nigerian and US stock research in one place. See exactly why a
          stock is performing well, showing potential, or underperforming,
          in plain language, before you decide anything.
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <LinkButton href="/signup" className="px-6 py-3 text-base">
            Get started free
          </LinkButton>
          <Link
            href="#how-it-works"
            className="text-sm font-semibold text-text underline decoration-border underline-offset-4 hover:decoration-text"
          >
            See how it works
          </Link>
        </div>
      </div>
      <div className="flex justify-center lg:justify-end">
        <HeroVisual />
      </div>
    </section>
  );
}
