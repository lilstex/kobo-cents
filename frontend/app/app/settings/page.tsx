import { Settings } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Settings — Kobo & Cents" };

// ChangePasswordForm (components/settings/ChangePasswordForm.tsx)
// already exists, built standalone in Phase 2, ready to mount here
// once this screen gets its real layout, deliberately not wired in
// yet since this page is still a Phase 3 placeholder.
export default function SettingsPage() {
  return (
    <EmptyState
      icon={Settings}
      title="Account settings"
      description="Change your password, switch theme, and manage your subscription from here. Landing soon."
    />
  );
}
