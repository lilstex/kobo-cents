"use client";

import { WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

// The shell-level half of the resilient-offline behavior from
// docs/frontend-architecture/05-app-plan.md: "a clear you're offline,
// showing the last data that loaded, state instead of a blank
// failure." This banner is the always-available part of that, true
// regardless of which /app screen is open. The richer per-screen
// version, an individual stock or overview page explicitly saying
// which specific data is stale, belongs to each data-fetching screen
// once it exists (Phase 4 onward), not this shared shell.
export function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    setIsOffline(!navigator.onLine);
    const goOffline = () => setIsOffline(true);
    const goOnline = () => setIsOffline(false);
    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="flex items-center justify-center gap-2 bg-down/10 px-4 py-2 text-center text-xs font-medium text-down">
      <WifiOff className="h-3.5 w-3.5" />
      You&apos;re offline. Showing what&apos;s already loaded.
    </div>
  );
}
