import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { SharedFavoritesList } from "@/components/app/share/SharedFavoritesList";
import { apiClient } from "@/lib/api/client";

// Next.js 16: dynamic route params are a Promise, not a plain object.
type Params = Promise<{ token: string }>;

export const metadata: Metadata = { title: "Shared favorites — Kobo & Cents" };

// An async Server Component fetching directly, per docs/backend-
// architecture/03-phases.md's Phase 7: unauthenticated on both ends,
// no client-side apiClient round trip needed. A missing or expired
// token is a real 404, per app/api/v1/share.py: Redis has already
// deleted the key, there's nothing left to distinguish "never
// existed" from "expired."
export default async function SharedFavoritesPage({ params }: { params: Params }) {
  const { token } = await params;
  const { data, response } = await apiClient.GET("/api/v1/share/{token}", {
    params: { path: { token } },
  });

  if (response.status === 404 || !data) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="mb-1 text-lg font-bold text-text">Shared favorites</h1>
      <SharedFavoritesList items={data.items} createdAt={data.created_at} />
    </div>
  );
}
