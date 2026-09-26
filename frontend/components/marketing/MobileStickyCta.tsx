import { LinkButton } from "@/components/ui";

/** Below the tablet breakpoint only, a CSS media query doing the
 * showing and hiding, never a scroll listener, per
 * docs/frontend-architecture/04-landing-page-indepth.md: a `display`
 * toggle driven by CSS costs nothing at runtime, a scroll-driven one
 * does. The page reserves matching bottom padding so this bar never
 * overlaps the final CTA section's own content. */
export function MobileStickyCta() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-bg/95 p-3 backdrop-blur sm:hidden">
      <LinkButton href="/signup" className="w-full justify-center py-3 text-base">
        Get started free
      </LinkButton>
    </div>
  );
}
