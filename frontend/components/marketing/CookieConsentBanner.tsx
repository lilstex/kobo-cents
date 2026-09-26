"use client";

import { useEffect, useState } from "react";
import {
  declineAnalyticsConsent,
  getStoredConsentChoice,
  grantAnalyticsConsent,
  initAnalyticsIfConsented,
} from "@/lib/analytics";
import { Button } from "@/components/ui";

/** Opt-in, per docs/frontend-architecture/07-phases.md's Sub-phase
 * 1.4: shown until a real choice is made, analytics stays off until
 * then. The strictly-necessary session cookie already works
 * regardless of this choice, it's never gated by it. */
export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const existing = getStoredConsentChoice();
    if (existing === "granted") {
      initAnalyticsIfConsented();
    } else if (existing === null) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  return (
    // bottom-16 on mobile, not bottom-0: the marketing pages' sticky
    // CTA bar sits at the very bottom of small screens too, per
    // components/marketing/MobileStickyCta.tsx, stacking flush would
    // bury the one button that bar exists to keep reachable, for
    // exactly the first-time mobile visitors both of these are for.
    // No sticky CTA exists past the sm breakpoint, so it reverts to
    // flush there.
    <div className="fixed inset-x-0 bottom-16 z-50 border-t border-border bg-surface px-4 py-4 sm:bottom-0 sm:px-6">
      <div className="mx-auto flex max-w-4xl flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs leading-relaxed text-muted">
          We use one strictly necessary cookie to keep you signed in, always
          on. Optional analytics cookies help us see what's actually used,
          only with your permission. See our{" "}
          <a href="/privacy" className="text-text underline">
            Privacy Policy
          </a>
          .
        </p>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="secondary"
            className="px-3 py-2 text-xs"
            onClick={() => {
              declineAnalyticsConsent();
              setVisible(false);
            }}
          >
            Decline
          </Button>
          <Button
            variant="primary"
            className="px-3 py-2 text-xs"
            onClick={() => {
              grantAnalyticsConsent();
              setVisible(false);
            }}
          >
            Accept analytics
          </Button>
        </div>
      </div>
    </div>
  );
}
