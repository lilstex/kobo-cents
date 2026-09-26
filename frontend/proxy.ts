import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Named proxy.ts, not middleware.ts: Next.js 16 deprecated and
// renamed the middleware.js file convention to proxy.js, same
// behavior, different file and export name, per
// node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md.
//
// A UX gate, not the real security boundary, per
// docs/frontend-architecture/04-landing-page-indepth.md: has_session
// is a plain, forgeable cookie, checked here only to avoid ever
// rendering a logged-out visitor into the authenticated shell. The
// real check happens wherever an /app page fetches real data against
// the backend, which validates the actual Redis-backed session.
export function proxy(request: NextRequest) {
  if (!request.cookies.has("has_session")) {
    return NextResponse.redirect(new URL("/", request.url));
  }
}

export const config = {
  matcher: ["/app/:path*"],
};
