/** Layout-shaped skeletons, never a spinner, per
 * docs/frontend-architecture/05-app-plan.md: a spinner reads as
 * inconsistent with a dense, tabular, precision-oriented system. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-surface ${className}`} />;
}
