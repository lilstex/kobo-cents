"use client";

import { Share, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Button, Card } from "@/components/ui";
import { useEngagementMilestoneReached } from "@/lib/installMilestone";

// beforeinstallprompt isn't in the standard DOM lib types.
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISSED_KEY = "kc_install_dismissed";

function isIosSafari(): boolean {
  const ua = window.navigator.userAgent;
  const isIos = /iphone|ipad|ipod/i.test(ua);
  const isStandaloneAlready = (window.navigator as { standalone?: boolean }).standalone === true;
  return isIos && !isStandaloneAlready;
}

/** Android/Chrome gets the real, captured beforeinstallprompt, fired
 * as a custom banner instead of letting the browser's own timing
 * decide. iOS Safari has no such event, a real platform limitation,
 * not a bug to work around, so it gets an instructional overlay
 * instead, the closest iOS actually allows. Both wait for the same
 * engagement milestone and can be dismissed for the session, per
 * docs/frontend-architecture/05-app-plan.md's Sub-phase 3.4. */
export function InstallPrompt() {
  const milestoneReached = useEngagementMilestoneReached();
  const [deferredEvent, setDeferredEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [showIosOverlay, setShowIosOverlay] = useState(false);

  useEffect(() => {
    try {
      setDismissed(sessionStorage.getItem(DISMISSED_KEY) === "1");
    } catch {
      // Leave it false, worst case the prompt shows once more than ideal.
    }
    setShowIosOverlay(isIosSafari());

    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setDeferredEvent(event as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
  }, []);

  function dismiss() {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISSED_KEY, "1");
    } catch {
      // Nothing to fall back to, it just asks again next session.
    }
  }

  async function install() {
    if (!deferredEvent) return;
    await deferredEvent.prompt();
    await deferredEvent.userChoice;
    setDeferredEvent(null);
    dismiss();
  }

  if (!milestoneReached || dismissed) return null;

  if (deferredEvent) {
    return (
      <Card className="fixed inset-x-4 bottom-20 z-40 flex items-center justify-between gap-3 sm:inset-x-auto sm:right-4 sm:bottom-4 sm:w-80">
        <p className="text-sm text-text">Install Kobo & Cents for quicker, full-screen access.</p>
        <div className="flex shrink-0 items-center gap-2">
          <Button onClick={install} className="px-3 py-1.5 text-xs">
            Install
          </Button>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Dismiss"
            className="text-muted hover:text-text"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </Card>
    );
  }

  if (showIosOverlay) {
    return (
      <Card className="fixed inset-x-4 bottom-20 z-40 flex items-center justify-between gap-3 sm:inset-x-auto sm:right-4 sm:bottom-4 sm:w-80">
        <p className="text-sm text-text">
          Install Kobo & Cents: tap <Share className="mb-0.5 inline h-4 w-4" aria-hidden />{" "}
          Share, then &quot;Add to Home Screen.&quot;
        </p>
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss"
          className="text-muted hover:text-text"
        >
          <X className="h-4 w-4" />
        </button>
      </Card>
    );
  }

  return null;
}
