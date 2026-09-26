import { Zap } from "lucide-react";

/** The Zap icon, brand-green left border, and the backend's own
 * generated sentence rendered as prose, per docs/frontend-
 * architecture/06-design.md, never a bullet list of the numbers
 * already shown in the metric cards above it. */
export function ExplainabilityPanel({ bucket, explanation }: { bucket: string | null; explanation: string }) {
  const label =
    bucket === "well"
      ? "performing well"
      : bucket === "potential"
        ? "showing potential"
        : bucket === "under"
          ? "underperforming"
          : "";

  return (
    <div className="mb-4 rounded-lg border border-border border-l-[3px] border-l-brand bg-surface p-3.5">
      <div className="mb-2 flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-brand">
        <Zap className="h-3.5 w-3.5" />
        {label ? `Why "${label}"` : "Why this score"}
      </div>
      <p className="text-[13px] leading-relaxed text-text">{explanation}</p>
    </div>
  );
}
