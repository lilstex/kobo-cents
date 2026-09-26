"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";

// The full MDX article, rendered in place, per docs/frontend-
// architecture/05-app-plan.md: "opens the full MDX content in an
// in-app drawer rather than navigating away to the public /glossary
// page and losing the user's place." `content` is the already-
// server-rendered <MDXRemote> output for this term, passed down from
// app/app/stocks/[ticker]/page.tsx (an async Server Component), since
// next-mdx-remote/rsc's MDXRemote only renders on the server, the
// same source the public glossary pages already use.
export function GlossaryDrawer({
  term,
  content,
  onClose,
}: {
  term: string;
  content: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[60] flex items-end bg-black/55 sm:items-center sm:justify-center">
      <div className="max-h-[85vh] w-full overflow-y-auto rounded-t-2xl border-t border-border bg-surface p-5 pb-8 sm:max-w-lg sm:rounded-2xl sm:border">
        <div className="mb-4 flex items-start justify-between gap-3">
          <h3 className="text-lg font-bold text-text">{term}</h3>
          <button type="button" onClick={onClose} aria-label="Close" className="text-muted">
            <X className="h-5 w-5" />
          </button>
        </div>
        <article className="prose-glossary flex flex-col gap-4 text-sm leading-relaxed text-text [&_h2]:mt-2 [&_h2]:text-base [&_h2]:font-semibold [&_p]:text-text">
          {content}
        </article>
      </div>
    </div>
  );
}
