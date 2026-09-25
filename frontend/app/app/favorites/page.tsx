import { Heart } from "lucide-react";
import type { Metadata } from "next";
import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Favorites — Kobo & Cents" };

export default function FavoritesPage() {
  return (
    <EmptyState
      icon={Heart}
      title="Your watchlist lives here"
      description="Add any stock as watching or owned and it shows up on this page. Landing soon."
    />
  );
}
