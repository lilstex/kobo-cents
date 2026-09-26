import type { Metadata } from "next";
import { FavoritesView } from "@/components/app/favorites/FavoritesView";

export const metadata: Metadata = { title: "Favorites — Kobo & Cents" };

export default function FavoritesPage() {
  return <FavoritesView />;
}
