import type { Metadata } from "next";
import { SignupForm } from "@/components/auth/SignupForm";
import { getLegalDoc } from "@/lib/legal";

export const metadata: Metadata = { title: "Sign up — Kobo & Cents" };

export default function SignupPage() {
  // The exact terms version stamped at signup, per docs/backend-
  // architecture/03-phases.md Sub-phase 1.1's compliance record, read
  // from the same source the /terms page itself renders, never a
  // hardcoded duplicate that could drift from what's actually shown.
  const { version } = getLegalDoc("terms");
  return <SignupForm termsVersion={version} />;
}
