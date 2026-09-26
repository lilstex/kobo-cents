import type { Metadata } from "next";
import Link from "next/link";
import { MDXRemote } from "next-mdx-remote/rsc";
import { notFound } from "next/navigation";
import { getAllGlossaryTerms, getGlossaryTermBySlug } from "@/lib/glossary";
import { definedTermSchema } from "@/lib/structured-data";

type Params = Promise<{ slug: string }>;

export function generateStaticParams() {
  return getAllGlossaryTerms().map((term) => ({ slug: term.slug }));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const term = getGlossaryTermBySlug(slug);
  if (!term) return {};
  return {
    title: `${term.term} — Kobo & Cents glossary`,
    description: term.shortDefinition,
  };
}

export default async function GlossaryTermPage({ params }: { params: Params }) {
  const { slug } = await params;
  const term = getGlossaryTermBySlug(slug);
  if (!term) notFound();

  return (
    <main className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: JSON.stringify(definedTermSchema(term)) }}
      />
      <Link href="/glossary" className="text-xs font-medium text-muted hover:text-text">
        &larr; Glossary
      </Link>
      <h1 className="mb-2 mt-4 text-2xl font-extrabold text-text sm:text-3xl">{term.term}</h1>
      <p className="mb-8 text-sm leading-relaxed text-muted">{term.shortDefinition}</p>
      <article className="prose-glossary flex flex-col gap-4 text-sm leading-relaxed text-text [&_h2]:mt-4 [&_h2]:text-base [&_h2]:font-semibold [&_p]:text-text">
        <MDXRemote source={term.body} />
      </article>
    </main>
  );
}
