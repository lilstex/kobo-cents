"use client";

/** Horizontal-scroll chip row, per docs/frontend-architecture/
 * 06-design.md: outlined, the active chip taking the full --text
 * color border rather than --brand, sector is a classification axis
 * independent of the bucket system, not another semantic color. */
export function SectorChips({
  sectors,
  selected,
  onSelect,
}: {
  sectors: string[];
  selected: string | null;
  onSelect: (sector: string | null) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-3.5" style={{ scrollbarWidth: "none" }}>
      <button
        type="button"
        onClick={() => onSelect(null)}
        className={`shrink-0 whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-semibold ${
          selected === null ? "border-text text-text" : "border-border text-muted"
        }`}
      >
        All sectors
      </button>
      {sectors.map((sector) => (
        <button
          key={sector}
          type="button"
          onClick={() => onSelect(sector)}
          className={`shrink-0 whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-semibold ${
            selected === sector ? "border-text text-text" : "border-border text-muted"
          }`}
        >
          {sector}
        </button>
      ))}
    </div>
  );
}
