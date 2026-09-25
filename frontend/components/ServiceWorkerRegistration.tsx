"use client";

import { useEffect } from "react";

/** Registers public/sw.js, per docs/frontend-architecture/05-app-plan.md's
 * Sub-phase 3.5. Skipped outside production: a cached module during
 * local development would otherwise serve stale code over a Turbopack
 * hot-reload, actively fighting the dev workflow instead of helping
 * a real repeat visitor. */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // A failed registration degrades to no offline caching, not a
      // broken app, nothing here needs surfacing to the user.
    });
  }, []);

  return null;
}
