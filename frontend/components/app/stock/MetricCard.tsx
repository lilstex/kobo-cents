import { Card } from "@/components/ui";
import type { components } from "@/lib/api/schema";
import { CATEGORY_LABELS, formatMetricValue } from "@/lib/metricFormat";

type CategoryBlock = components["schemas"]["CategoryBlock"];
type GlossaryPayloadEntry = components["schemas"]["GlossaryPayloadEntry"];

/** One card per metric category, per docs/backend-architecture/01.md:
 * the category's own sector percentile in the header, each metric's
 * value and percentile below, the label itself the tap target that
 * opens the glossary sheet, per docs/frontend-architecture/
 * 05-app-plan.md's Sub-phase 5.3. */
export function MetricCard({
  category,
  glossary,
  onSelectMetric,
}: {
  category: CategoryBlock;
  glossary: Record<string, GlossaryPayloadEntry>;
  onSelectMetric: (metricKey: string) => void;
}) {
  return (
    <Card className="mb-2.5">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[13px] font-bold text-text">
          {CATEGORY_LABELS[category.category] ?? category.category}
        </span>
        {category.score !== null ? (
          <span className="font-mono text-[11px] font-bold text-brand">
            {Math.round(category.score)}th pctl
          </span>
        ) : null}
      </div>
      {category.metrics.map((metric) => (
        <div
          key={metric.key}
          className="flex items-center justify-between border-b border-border py-1.5 text-xs last:border-b-0"
        >
          <button
            type="button"
            onClick={() => onSelectMetric(metric.key)}
            className="border-b border-dashed border-border text-left text-muted hover:text-text"
          >
            {glossary[metric.key]?.term ?? metric.label}
          </button>
          <span className="font-mono font-semibold text-text">
            {formatMetricValue(metric.key, metric.value)}
          </span>
        </div>
      ))}
    </Card>
  );
}
