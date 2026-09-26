import type { MetadataRoute } from "next";

// start_url is /app, not /, per docs/frontend-architecture/05-app-plan.md:
// a PWA install is something a committed, already-signed-up user
// does, opening the installed icon should land them in the product.
// If the session has actually expired by then, proxy.ts redirects to
// / exactly as it would for any other unauthenticated hit on /app.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kobo & Cents",
    short_name: "Kobo & Cents",
    description: "Nigerian and US stock research. Never a trading platform.",
    start_url: "/app",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#0b0e0c",
    theme_color: "#0b0e0c",
    icons: [
      { src: "/pwa/icon-192-any.png", sizes: "192x192", type: "image/png", purpose: "any" },
      {
        src: "/pwa/icon-192-maskable.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      { src: "/pwa/icon-512-any.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/pwa/icon-512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
