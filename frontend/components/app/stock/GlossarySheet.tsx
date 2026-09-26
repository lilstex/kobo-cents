"use client";

import { ChevronRight, X } from "lucide-react";

// A bottom sheet, per docs/frontend-architecture/06-design.md's
// glossary popover mockup, reused here rather than an anchored
// tooltip: no per-label position measuring, works identically at
// every viewport width, and mirrors the same sheet mechanism this
// design system already uses elsewhere (the paywall modal), one
// pattern instead of two.
export function GlossarySheet({
  term,
  shortDefinition,
  onClose,
  onOpenFullEntry,
}: {
  term: string;
  shortDefinition: string;
  onClose: () => void;
  onOpenFullEntry: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/55" onClick={onClose}>
      <div
        className="w-full rounded-t-2xl border-t border-border bg-surface p-5 pb-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-2 flex items-start justify-between gap-3">
          <h3 className="text-sm font-bold text-text">{term}</h3>
          <button type="button" onClick={onClose} aria-label="Close" className="text-muted">
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs leading-relaxed text-muted">{shortDefinition}</p>
        <button
          type="button"
          onClick={onOpenFullEntry}
          className="mt-3 inline-flex items-center gap-1 font-mono text-[11px] font-bold text-brand"
        >
          Full glossary entry
          <ChevronRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
