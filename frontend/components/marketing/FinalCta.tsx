import { LinkButton } from "@/components/ui";

export function FinalCta() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-5 px-6 py-16 text-center sm:py-20">
        <h2 className="text-2xl font-bold text-text sm:text-3xl">
          See what a stock is actually telling you.
        </h2>
        <LinkButton href="/signup" className="px-6 py-3 text-base">
          Get started free
        </LinkButton>
      </div>
    </section>
  );
}
