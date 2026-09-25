import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p>A ShotNub Solutions product</p>
        <nav className="flex gap-6">
          <Link href="#trust" className="hover:text-text">
            About
          </Link>
          <Link href="/privacy" className="hover:text-text">
            Privacy Policy
          </Link>
          <Link href="/terms" className="hover:text-text">
            Terms of Service
          </Link>
        </nav>
      </div>
    </footer>
  );
}
