export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  // Relative URL only per Rule R7 - Vite dev proxy forwards to http://127.0.0.1:8000
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
