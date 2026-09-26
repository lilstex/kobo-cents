import type { Metadata } from "next";
import { Suspense } from "react";
import { CompareView } from "@/components/app/compare/CompareView";
import { Skeleton } from "@/components/ui";

export const metadata: Metadata = { title: "Compare — Kobo & Cents" };

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <div className="px-4 pt-4 sm:px-6 sm:pt-6">
          <Skeleton className="h-8 w-full" />
        </div>
      }
    >
      <CompareView />
    </Suspense>
  );
}
