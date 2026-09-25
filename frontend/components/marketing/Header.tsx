import Image from "next/image";
import Link from "next/link";
import { LinkButton } from "@/components/ui";

/** Sticky on scroll so the primary CTA stays reachable on a long
 * page, per docs/frontend-architecture/03-landing-page.md. One nav
 * link, one primary button, nothing competing with the single
 * conversion goal. */
export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
        <Link href="/" className="flex shrink-0 items-center">
          <Image
            src="/wordmark-dark.svg"
            alt="Kobo & Cents"
            width={140}
            height={26}
            priority
            className="theme-dark-only w-32 sm:w-40"
          />
          <Image
            src="/wordmark-light.svg"
            alt="Kobo & Cents"
            width={140}
            height={26}
            priority
            className="theme-light-only w-32 sm:w-40"
          />
        </Link>
        <nav className="flex items-center gap-4 sm:gap-5">
          {/* Below sm, only the primary action shows, per the same
           * mobile-first discipline as everything else in this system,
           * not a reason to cram a second link into no space. */}
          <Link
            href="/login"
            className="hidden text-sm font-medium text-muted hover:text-text sm:inline"
          >
            Sign in
          </Link>
          <LinkButton href="/signup" className="px-3 py-2 text-sm sm:px-4 sm:py-2.5">
            Get started free
          </LinkButton>
        </nav>
      </div>
    </header>
  );
}
