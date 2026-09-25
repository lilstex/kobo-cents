"use client";

import { useEffect, useState } from "react";

// Reads the plain, non-httpOnly has_session cookie the backend sets
// alongside the real session cookie, per docs/frontend-architecture/
// 04-landing-page-indepth.md: a UX hint only, checked client-side
// after hydration so the landing page itself stays one static file,
// never trusted for the actual access check. Starts false so server
// and client render the same logged-out markup on first paint, then
// flips after mount, the documented brief flash tradeoff.
export function useHasSession(): boolean {
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    setHasSession(document.cookie.split("; ").some((entry) => entry.startsWith("has_session=")));
  }, []);

  return hasSession;
}
