import type { ReactNode } from "react";

type BucketVariant = "well" | "potential" | "under";

const LABELS: Record<BucketVariant, string> = {
  well: "Performing well",
  potential: "Showing potential",
  under: "Underperforming",
};

// Outlined, never filled. "potential" stays --muted, deliberately not
// a third semantic color, per docs/frontend-architecture/01.md: green
// means gain, coral means loss, a bucket is a classification, not a
// price movement, and doesn't borrow that color language.
const VARIANTS: Record<BucketVariant, string> = {
  well: "border-brand text-brand",
  potential: "border-border text-muted",
  under: "border-down text-down",
};

export function BucketChip({
  variant,
  children,
}: {
  variant: BucketVariant;
  children?: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-wider ${VARIANTS[variant]}`}
    >
      {children ?? LABELS[variant]}
    </span>
  );
}
