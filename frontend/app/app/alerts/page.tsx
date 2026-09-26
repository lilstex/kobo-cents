import type { Metadata } from "next";
import { AlertsView } from "@/components/app/alerts/AlertsView";

export const metadata: Metadata = { title: "Alerts — Kobo & Cents" };

export default function AlertsPage() {
  return <AlertsView />;
}
