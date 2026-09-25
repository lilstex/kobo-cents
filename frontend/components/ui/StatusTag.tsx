type Status = "watching" | "owned";

const LABELS: Record<Status, string> = {
  watching: "Watching",
  owned: "Owned",
};

// Watching: outlined in --border, --muted text. Owned: outlined in
// --brand, --brand text. Matches docs/frontend-architecture/06-design.md
// exactly, has to read at a glance in a list, never buried in a detail
// view, per docs/01_product.md.
const VARIANTS: Record<Status, string> = {
  watching: "border-border text-muted",
  owned: "border-brand text-brand",
};

export function StatusTag({ status }: { status: Status }) {
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 font-mono text-[9.5px] font-bold uppercase tracking-wide ${VARIANTS[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
