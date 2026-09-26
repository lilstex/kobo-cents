import type { Metadata } from "next";
import { MDXRemote } from "next-mdx-remote/rsc";
import { DraftLegalNotice } from "@/components/marketing/DraftLegalNotice";
import { getLegalDoc } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Privacy Policy — Kobo & Cents",
  description: "How Kobo & Cents collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  const doc = getLegalDoc("privacy");
  return (
    <main className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
      <h1 className="mb-1 text-2xl font-extrabold text-text sm:text-3xl">Privacy Policy</h1>
      <p className="mb-6 font-mono text-xs text-muted">
        Version {doc.version} &middot; effective {doc.effectiveDate}
      </p>
      <DraftLegalNotice />
      <article className="flex flex-col gap-4 text-sm leading-relaxed text-text [&_h2]:mt-4 [&_h2]:text-base [&_h2]:font-semibold [&_strong]:text-text">
        <MDXRemote source={doc.body} />
      </article>
    </main>
  );
}
