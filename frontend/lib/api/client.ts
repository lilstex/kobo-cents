import createClient from "openapi-fetch";
import type { paths } from "./schema";

/**
 * Every backend call goes through this client, typed against
 * schema.d.ts, generated from the backend's own OpenAPI schema, per
 * docs/frontend-architecture/00.md: the API contract is never
 * hand-mirrored. Regenerate schema.d.ts with `npm run generate:types`
 * whenever the backend's API surface changes, and commit the result.
 */
export const apiClient = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  // The frontend and backend are different origins in every real
  // environment (different ports locally, different subdomains in
  // production), and fetch's default credentials mode, "same-origin",
  // silently drops both outgoing cookies and incoming Set-Cookie
  // headers on a cross-origin request. Without this, login "succeeds"
  // (a 200 comes back) but the session and has_session cookies never
  // actually get stored, and every following request is anonymous, a
  // real gap only surfaced by driving a real signup-to-/app flow
  // through an actual browser rather than a backend-only test client.
  credentials: "include",
});
