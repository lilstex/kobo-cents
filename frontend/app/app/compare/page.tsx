import { GitCompare } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Compare — Kobo & Cents" };

export default function ComparePage() {
  return (
    <EmptyState
      icon={GitCompare}
      title="Compare stocks side by side"
      description="Pick two or three stocks and see the same metric categories in the same order, a straight read across a row. Landing soon."
    />
  );
}
