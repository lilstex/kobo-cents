import type { Metadata } from "next";
import { Suspense } from "react";
import { VerifyStatus } from "@/components/auth/VerifyStatus";

export const metadata: Metadata = { title: "Verify your email — Kobo & Cents" };

export default function VerifyPage() {
  // useSearchParams (reading ?token= / ?email=) requires a Suspense
  // boundary in the App Router, a real Next.js build requirement, not
  // an optional nicety.
  return (
    <Suspense fallback={<p className="text-center text-sm text-muted">Loading…</p>}>
      <VerifyStatus />
    </Suspense>
  );
}
