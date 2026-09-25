"use client";

import posthog from "posthog-js";

const CONSENT_KEY = "kc_analytics_consent";

function readConsent(): string | null {
  try {
    return localStorage.getItem(CONSENT_KEY);
  } catch {
    return null;
  }
}

function writeConsent(value: string): void {
  try {
    localStorage.setItem(CONSENT_KEY, value);
  } catch {
    // Private browsing or blocked storage: the choice just won't
    // persist across a reload, not worth failing the interaction for.
  }
}

/** PostHog only initializes after opt-in consent, per
 * docs/frontend-architecture/07-phases.md's Sub-phase 1.4. The
 * strictly-necessary session cookie is never gated by this, only
 * analytics is. A no-op without a configured key, same dev-safe
 * default the backend uses. */
export function initAnalyticsIfConsented(): void {
  if (typeof window === "undefined") return;
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) return;
  if (readConsent() !== "granted") return;

  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://app.posthog.com",
    person_profiles: "identified_only",
  });
}

export function grantAnalyticsConsent(): void {
  writeConsent("granted");
  initAnalyticsIfConsented();
}

export function declineAnalyticsConsent(): void {
  writeConsent("declined");
}

export function getStoredConsentChoice(): "granted" | "declined" | null {
  if (typeof window === "undefined") return null;
  return readConsent() as "granted" | "declined" | null;
}
