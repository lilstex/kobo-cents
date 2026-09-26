/** FastAPI's own two error shapes: a plain HTTPException gives
 * `{ detail: string }`, a Pydantic validation failure gives
 * `{ detail: [{ msg: string, ... }] }`. Every auth form's error
 * copy comes from here, so a backend message ("An account with this
 * email already exists") reaches the user directly instead of a
 * generic fallback hiding it. */
export function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === "string") {
      return detail[0].msg;
    }
  }
  return fallback;
}
