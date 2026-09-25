import { WifiOff } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "You're offline — Kobo & Cents" };

// The service worker's precached fallback (app/sw.ts) for a
// navigation that fails completely offline with nothing cached for
// that specific page, per docs/frontend-architecture/05-app-plan.md's
// Sub-phase 3.5: a real, considered state, not a blank browser error.
export default function OfflinePage() {
  return (
    <div className="flex min-h-full items-center justify-center px-6">
      <EmptyState
        icon={WifiOff}
        title="You're offline"
        description="This page hasn't loaded before, so there's nothing saved to show yet. Reconnect and try again."
      />
    </div>
  );
}
