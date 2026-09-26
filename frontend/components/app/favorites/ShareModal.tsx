"use client";

import { Check, Copy, Share2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

function formatCountdown(expiresAt: string): string {
  const remainingMs = new Date(expiresAt).getTime() - Date.now();
  if (remainingMs <= 0) return "Expired";
  const hours = Math.floor(remainingMs / (60 * 60 * 1000));
  const minutes = Math.floor((remainingMs % (60 * 60 * 1000)) / (60 * 1000));
  return `Expires in ${hours}h ${minutes}m`;
}

/** Generates the 24-hour Redis-backed link on mount, per
 * docs/frontend-architecture/07-phases.md's Phase 9: the countdown
 * reads the real `expires_at` the backend returns, ticking every 30
 * seconds, not a static "24 hours" label that would drift from the
 * truth as the link ages. */
export function ShareModal({ onClose }: { onClose: () => void }) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [countdown, setCountdown] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function create() {
      const { data, error: apiError } = await apiClient.POST("/api/v1/share", {});
      if (cancelled) return;
      if (apiError || !data) {
        setError(extractErrorMessage(apiError, "Could not generate a share link, try again."));
        return;
      }
      setShareUrl(data.share_url);
      setExpiresAt(data.expires_at);
    }

    create();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!expiresAt) return;
    setCountdown(formatCountdown(expiresAt));
    const interval = setInterval(() => setCountdown(formatCountdown(expiresAt)), 30_000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  async function handleCopy() {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard permission can be denied, or the API can be
      // unavailable outside a secure context, a real failure mode
      // worth a message rather than a button that silently does
      // nothing.
      setError("Could not copy automatically, select and copy the link above instead.");
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/55" onClick={onClose}>
      <div
        className="w-full rounded-t-2xl border-t border-border bg-surface p-5 pb-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-2.5 flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-brand">
          <Share2 className="h-3.5 w-3.5" />
          Share your favorites
        </div>
        <h3 className="mb-2 text-lg font-bold text-text">A snapshot, not a live view</h3>
        <p className="mb-4 text-sm text-muted">
          Anyone with this link can see your favorites list as it looks right now. It stops
          working in 24 hours, no account needed on their end.
        </p>

        {error ? <p className="mb-3 text-xs text-down">{error}</p> : null}

        {!error && !shareUrl ? (
          <div className="mb-4 h-10 animate-pulse rounded-lg bg-border/40" />
        ) : null}

        {shareUrl ? (
          <div className="mb-4">
            <div className="flex items-center gap-2 rounded-lg border border-border bg-bg px-3 py-2.5">
              <span className="min-w-0 flex-1 truncate font-mono text-[12px] text-text">
                {shareUrl}
              </span>
              <button
                type="button"
                onClick={handleCopy}
                aria-label="Copy share link"
                className="shrink-0 text-muted hover:text-brand"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-brand" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="mt-2 font-mono text-[11px] text-muted">{countdown}</p>
          </div>
        ) : null}

        <Button onClick={handleCopy} disabled={!shareUrl} className="w-full">
          {copied ? "Copied" : "Copy link"}
        </Button>
      </div>
    </div>
  );
}
