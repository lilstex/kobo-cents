"use client";

import type { Market } from "@/lib/sectors";

const OPTIONS: { value: Market; label: string }[] = [
  { value: "ng", label: "NIGERIA" },
  { value: "us", label: "UNITED STATES" },
];

/** A pill control, per docs/frontend-architecture/06-design.md, the
 * active side filled brand-green. Switching markets clears the
 * sector filter, the two taxonomies don't share sector names, per
 * docs/01_product.md, so a sector chosen in one market means nothing
 * in the other. */
export function MarketToggle({
  market,
  onChange,
  className = "",
}: {
  market: Market;
  onChange: (market: Market) => void;
  className?: string;
}) {
  return (
    <div className={`flex gap-0.5 rounded-full border border-border bg-surface p-0.5 ${className}`}>
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`flex-1 rounded-full py-1.5 font-mono text-xs font-bold tracking-wide ${
            market === option.value ? "bg-brand text-bg" : "text-muted"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
