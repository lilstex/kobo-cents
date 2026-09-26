"use client";

import { useReportWebVitals } from "next/web-vitals";
import posthog from "posthog-js";

/** Confirms the lab numbers (Lighthouse CI) against real visitor
 * traffic, per docs/frontend-architecture/07-phases.md's Sub-phase
 * 1.6. posthog.capture is itself a no-op until the user has actually
 * granted analytics consent and posthog.init has run, per the cookie
 * consent gating in lib/analytics.ts, so this never sends anything
 * before that. */
export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    posthog.capture("web_vital", {
      metric_name: metric.name,
      value: metric.value,
      rating: metric.rating,
      page: window.location.pathname,
    });
  });
  return null;
}
