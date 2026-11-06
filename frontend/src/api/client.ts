/** Error with the backend's own message (`detail`) so the UI can show something useful. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: unknown }).msg) : String(d))).join("; ");
    }
  } catch {
    // body was not JSON
  }
  return `${response.status} ${response.statusText}`.trim();
}

/**
 * Relative URL only: the Vite dev proxy forwards /api to http://127.0.0.1:8000.
 * Pass a plain object as `body` to send JSON, or FormData to upload (the browser sets the boundary).
 */
export async function apiClient<T>(
  endpoint: string,
  options: Omit<RequestInit, "body"> & { body?: unknown } = {},
): Promise<T> {
  const { body, headers, ...rest } = options;
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  let response: Response;
  try {
    response = await fetch(endpoint, {
      ...rest,
      headers: { ...(body !== undefined && !isForm ? { "Content-Type": "application/json" } : {}), ...headers },
      body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("backend_unreachable", 0);
  }
  if (!response.ok) throw new ApiError(await readError(response), response.status);
  return response.json() as Promise<T>;
}
