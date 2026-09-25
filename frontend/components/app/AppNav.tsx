"use client";

import { GitCompare, Heart, Lock, Settings, TrendingUp } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";

type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
};

// Five items, the practical ceiling for a bottom bar before it gets
// cramped, per docs/frontend-architecture/05-app-plan.md. Alerts
// shows Lock rather than Bell until real entitlement data reaches the
// frontend (Phase 8's paywall work), a visible hint rather than a
// hidden gate, so it defaults to the paid-locked icon rather than
// assuming free access it can't yet verify.
const NAV_ITEMS: NavItem[] = [
  { href: "/app", label: "Markets", icon: TrendingUp },
  { href: "/app/compare", label: "Compare", icon: GitCompare },
  { href: "/app/favorites", label: "Favorites", icon: Heart },
  { href: "/app/alerts", label: "Alerts", icon: Lock },
  { href: "/app/settings", label: "Settings", icon: Settings },
];

function isActive(pathname: string, href: string): boolean {
  return href === "/app" ? pathname === "/app" : pathname.startsWith(href);
}

/** Bottom tab bar under 640px, fixed left sidebar at 640px and up,
 * one shared item list and active-state logic, the breakpoint switch
 * itself handled by Tailwind's `sm:` utilities (exactly 640px by
 * default) rather than a duplicated JS media-query listener, per
 * docs/frontend-architecture/05-app-plan.md's single-threshold rule. */
export function AppNav() {
  const pathname = usePathname();

  return (
    <>
      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-surface sm:hidden"
      >
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium ${
                active ? "text-brand" : "text-muted"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <nav
        aria-label="Primary"
        className="fixed inset-y-0 left-0 z-40 hidden w-56 flex-col gap-1 border-r border-border bg-surface p-4 sm:flex"
      >
        <Link href="/app" className="mb-6 flex items-center px-2">
          <Image
            src="/wordmark-dark.svg"
            alt="Kobo & Cents"
            width={128}
            height={24}
            className="theme-dark-only"
          />
          <Image
            src="/wordmark-light.svg"
            alt="Kobo & Cents"
            width={128}
            height={24}
            className="theme-light-only"
          />
        </Link>
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${
                active ? "bg-bg text-brand" : "text-muted hover:text-text"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
