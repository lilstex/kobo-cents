/** Unmissable on purpose, per docs/frontend-architecture/
 * 04-landing-page-indepth.md: the content inventory and technical
 * scaffolding for these pages is real, the clause wording isn't
 * final, and nothing here should read as though it already had a
 * legal review it hasn't had yet. */
export function DraftLegalNotice() {
  return (
    <div className="mb-8 rounded-lg border border-down/40 bg-down/10 px-4 py-3 text-xs leading-relaxed text-text">
      <strong className="text-down">Draft, pending legal review.</strong> This
      page's structure and content are real, but the exact wording has
      not yet been reviewed by a lawyer or checked against NDPR. Do not
      treat this as final legal text.
    </div>
  );
}
