"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { FormError } from "@/components/auth/FormError";
import { Button } from "@/components/ui";
import { apiClient } from "@/lib/api/client";
import { extractErrorMessage } from "@/lib/api/errors";

// docs/frontend-architecture/07-phases.md's Sub-phase 2.1 describes
// "code entry plus a resend action." The backend actually built in
// Phase 2 (docs/backend-architecture/03-phases.md) uses a long token
// delivered as an email link, not a short typed code, the more secure
// and more common real-world pattern for this exact flow. This page
// follows what the backend actually does: a token in the URL (the
// user clicked the email link) verifies automatically; no token shown
// yet means "check your email," with the resend action the phases doc
// asked for, calling the real /auth/resend-verification endpoint.
type Status = "waiting" | "verifying" | "success" | "error";

export function VerifyStatus() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const email = searchParams.get("email");
  const [status, setStatus] = useState<Status>(token ? "verifying" : "waiting");
  const [error, setError] = useState<string | null>(null);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  // The token is single-use server-side, so this must only ever POST
  // once per token: React's Strict Mode double-invokes effects in
  // development, and without this guard the first call consumes the
  // token successfully while the second call's "already used" error
  // is what actually lands in state, showing a false failure for an
  // account that in fact got verified. A ref (not state) survives the
  // Strict Mode remount that would reset a state-based guard.
  const verifiedTokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token || verifiedTokenRef.current === token) return;
    verifiedTokenRef.current = token;
    apiClient.POST("/api/v1/auth/verify", { body: { token } }).then(({ error: apiError }) => {
      if (apiError) {
        setError(extractErrorMessage(apiError, "Could not verify this link."));
        setStatus("error");
      } else {
        setStatus("success");
      }
    });
  }, [token]);

  async function resend() {
    if (!email) return;
    setResendMessage(null);
    await apiClient.POST("/api/v1/auth/resend-verification", { body: { email } });
    setResendMessage("If that account needs verifying, a new email is on its way.");
  }

  if (status === "success") {
    return (
      <div className="flex flex-col gap-4 text-center">
        <h1 className="text-xl font-bold text-text">Email verified</h1>
        <p className="text-sm text-muted">You can sign in now.</p>
        <Button onClick={() => (window.location.href = "/login")}>Go to sign in</Button>
      </div>
    );
  }

  if (status === "verifying") {
    return <p className="text-center text-sm text-muted">Verifying…</p>;
  }

  return (
    <div className="flex flex-col gap-4 text-center">
      <h1 className="text-xl font-bold text-text">Check your email</h1>
      {status === "error" ? (
        <FormError message={error} />
      ) : (
        <p className="text-sm text-muted">
          We sent a verification link{email ? ` to ${email}` : ""}. Click it to activate your
          account.
        </p>
      )}
      {email ? (
        <Button variant="secondary" onClick={resend}>
          Resend the email
        </Button>
      ) : null}
      {resendMessage ? <p className="text-xs text-muted">{resendMessage}</p> : null}
      <Link href="/login" className="text-xs text-muted underline">
        Back to sign in
      </Link>
    </div>
  );
}
