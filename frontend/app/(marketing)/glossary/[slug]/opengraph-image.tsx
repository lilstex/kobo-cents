import { ImageResponse } from "next/og";
import { getGlossaryTermBySlug } from "@/lib/glossary";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// One template, per docs/frontend-architecture/04-landing-page-indepth.md,
// covering every glossary term automatically rather than a hand-built
// image per term. Same Terminal Precision system as the article
// preview cards, generated at request time here instead of ahead of
// time with the Pillow pipeline those use, next/og is the natural
// tool for a page that's one of many generated from the same shape.
export default async function GlossaryTermOgImage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const term = getGlossaryTermBySlug(slug);
  const archivoBold = await fetch(
    "https://fonts.gstatic.com/s/archivo/v25/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTTtDRp8A.ttf",
  ).then((res) => res.arrayBuffer());

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          backgroundColor: "#0B0E0C",
          padding: "72px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 6,
              backgroundColor: "#3ECF8E",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 22,
              fontWeight: 800,
              color: "#0B0E0C",
            }}
          >
            &amp;
          </div>
          <span style={{ fontSize: 20, color: "#8B968F", fontWeight: 700 }}>
            KOBO &amp; CENTS GLOSSARY
          </span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <span style={{ fontSize: 64, fontWeight: 800, color: "#E8ECE9" }}>
            {term?.term ?? "Glossary"}
          </span>
          <span style={{ fontSize: 26, color: "#8B968F", maxWidth: 900 }}>
            {term?.shortDefinition ?? ""}
          </span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [{ name: "Archivo", data: archivoBold, weight: 800 }],
    },
  );
}
