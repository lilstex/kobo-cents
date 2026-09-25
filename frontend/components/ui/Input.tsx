import { type InputHTMLAttributes, forwardRef } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

/** Focused input field, used from the auth screens through the
 * alert-rule form, per docs/frontend-architecture/01.md. */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, className = "", ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label ? (
          <label
            htmlFor={id}
            className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted"
          >
            {label}
          </label>
        ) : null}
        <input
          ref={ref}
          id={id}
          className={`rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-text outline-none placeholder:text-muted focus:border-brand ${className}`}
          {...props}
        />
        {error ? <span className="text-xs text-down">{error}</span> : null}
      </div>
    );
  },
);
Input.displayName = "Input";
