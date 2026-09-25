import { Lock } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Alerts — Kobo & Cents" };

export default function AlertsPage() {
  return (
    <EmptyState
      icon={Lock}
      title="Get told, not just able to check"
      description="A paid feature: notify you when a favorited stock's score changes or crosses a price threshold you set. Landing soon."
    />
  );
}
