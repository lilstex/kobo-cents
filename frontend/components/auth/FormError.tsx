/** One error-display pattern for every auth form, per
 * docs/frontend-architecture/07-phases.md's Sub-phase 2.3: specific,
 * actionable copy, never a generic "something went wrong." The
 * message itself comes from the caller, this component only owns the
 * presentation, so every form still writes its own real copy for
 * what actually happened. */
export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="rounded-lg border border-down/40 bg-down/10 px-3 py-2.5 text-sm text-down"
    >
      {message}
    </div>
  );
}
