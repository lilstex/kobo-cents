"use client";

import { useEffect, useState } from "react";

// The install prompt (Sub-phase 3.4) is deliberately not shown on
// first visit, per docs/frontend-architecture/05-app-plan.md: it
// surfaces after a real engagement milestone, favoriting a first
// stock, not immediately, when it's most likely dismissed as noise.
// Favorites itself is Phase 7 work and doesn't exist yet, so this is
// the reusable trigger Phase 7's "add to favorites" action will call;
// nothing in this codebase calls it yet, same standalone-until-wired
// pattern as ChangePasswordForm from Phase 2.
const MILESTONE_KEY = "kc_engagement_milestone";
const MILESTONE_EVENT = "kc:engagement-milestone";

export function markEngagementMilestone(): void {
  try {
    localStorage.setItem(MILESTONE_KEY, "1");
  } catch {
    // Private browsing or blocked storage: the install prompt simply
    // never appears this session, not worth failing the calling
    // action (adding a favorite) over.
  }
  window.dispatchEvent(new Event(MILESTONE_EVENT));
}

export function useEngagementMilestoneReached(): boolean {
  const [reached, setReached] = useState(false);

  useEffect(() => {
    try {
      setReached(localStorage.getItem(MILESTONE_KEY) === "1");
    } catch {
      // Leave it false: no worse than the pre-milestone state.
    }
    const onMilestone = () => setReached(true);
    window.addEventListener(MILESTONE_EVENT, onMilestone);
    return () => window.removeEventListener(MILESTONE_EVENT, onMilestone);
  }, []);

  return reached;
}
