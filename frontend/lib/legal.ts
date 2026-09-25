import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

export type LegalDoc = {
  version: string;
  effectiveDate: string;
  body: string;
};

const LEGAL_DIR = path.join(process.cwd(), "content", "legal");

export function getLegalDoc(name: "terms" | "privacy"): LegalDoc {
  const raw = fs.readFileSync(path.join(LEGAL_DIR, `${name}.mdx`), "utf-8");
  const { data, content } = matter(raw);
  return {
    version: data.version as string,
    effectiveDate: data.effectiveDate as string,
    body: content,
  };
}
