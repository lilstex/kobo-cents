import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/** Designed on purpose, not a placeholder default, per
 * docs/frontend-architecture/05-app-plan.md: an empty favorites list
 * or an empty alerts list both need real copy and a real next action. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <Icon className="h-8 w-8 text-muted" strokeWidth={2} />
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      <p className="max-w-xs text-xs leading-relaxed text-muted">{description}</p>
      {action ? <div className="mt-1.5">{action}</div> : null}
    </div>
  );
}
