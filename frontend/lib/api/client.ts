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
});
