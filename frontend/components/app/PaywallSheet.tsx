"use client";

import { Check, Lock } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

/** One modal/sheet, used identically by Alerts and Sharing, per
 * docs/frontend-architecture/07-phases.md's Sub-phase 8.1: never a
 * silent 403 (here, a 402), a real explanation of what upgrading
 * unlocks. "Upgrade" starts a real checkout (Paystack by default,
 * NG-first per docs/01_product.md) and redirects to the provider's
 * own hosted page; there is deliberately one button, not a provider
 * picker, matching the mockup exactly. */
export function PaywallSheet({ onClose }: { onClose: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleUpgrade() {
    setError(null);
    setLoading(true);
    const { data, error: apiError } = await apiClient.POST("/api/v1/subscriptions/checkout", {
      body: { provider: "paystack" },
    });
    setLoading(false);
    if (apiError || !data) {
      setError(extractErrorMessage(apiError, "Could not start checkout, try again."));
      return;
    }
    window.location.href = data.redirect_url;
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/55" onClick={onClose}>
      <div
        className="w-full rounded-t-2xl border-t border-border bg-surface p-5 pb-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-2.5 flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-brand">
          <Lock className="h-3.5 w-3.5" />
          Upgrade to unlock
        </div>
        <h3 className="mb-2 text-lg font-bold text-text">Never miss a move</h3>
        <p className="mb-4 text-sm text-muted">
          Alerts and sharing are both part of the paid tier. Here&apos;s what upgrading gets you:
        </p>
        <ul className="mb-5 flex flex-col gap-2">
          {[
            "Score and price alerts, by email",
            "Shareable favorites links",
            "Unlimited favorites",
          ].map((benefit) => (
            <li key={benefit} className="flex items-center gap-2 text-sm text-text">
              <Check className="h-3.5 w-3.5 shrink-0 text-brand" />
              {benefit}
            </li>
          ))}
        </ul>
        {error ? <p className="mb-3 text-xs text-down">{error}</p> : null}
        <Button onClick={handleUpgrade} disabled={loading} className="w-full">
          {loading ? "Starting checkout…" : "Upgrade"}
        </Button>
      </div>
    </div>
  );
}
