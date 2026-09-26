import type { Metadata } from "next";
import { Suspense } from "react";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";

export const metadata: Metadata = { title: "Reset password — Kobo & Cents" };

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<p className="text-center text-sm text-muted">Loading…</p>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
