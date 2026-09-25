import Link from "next/link";
import { type AnchorHTMLAttributes, type ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-opacity disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

// Primary fills with --brand; the dark ampersand on the brand-green
// icon mark already proved this pairing reads correctly in both
// themes, so the primary button's text reuses that same
// --bg-on---brand relationship rather than a new color decision.
const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-bg hover:opacity-90",
  secondary: "border border-border text-text hover:bg-surface",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant };

/** Primary and secondary buttons, per docs/frontend-architecture/01.md's
 * first component set. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => (
    <button ref={ref} className={`${BASE} ${VARIANTS[variant]} ${className}`} {...props} />
  ),
);
Button.displayName = "Button";

type LinkButtonProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  href: string;
  variant?: Variant;
};

/** Same visual language as Button, for the real navigation cases
 * ("Get started free" going to /signup), never a <button> with a
 * client-side router push standing in for a link. */
export function LinkButton({ variant = "primary", className = "", href, ...props }: LinkButtonProps) {
  return <Link href={href} className={`${BASE} ${VARIANTS[variant]} ${className}`} {...props} />;
}
