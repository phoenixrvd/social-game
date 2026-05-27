export type ApiError = Error & { status?: number }

function createApiError(message: string, status?: number): ApiError {
  const error = new Error(message) as ApiError
  error.status = status
  return error
}

function errorMessage(payload: unknown, fallback: string): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof (payload as { detail?: unknown }).detail === "string" &&
    (payload as { detail: string }).detail.trim()
  ) {
    return (payload as { detail: string }).detail.trim()
  }
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    Array.isArray((payload as { detail?: unknown }).detail)
  ) {
    return fallback
  }
  return fallback
}

export async function requestJson<T>(
  url: string,
  init?: RequestInit,
  fallbackError = "Anfrage fehlgeschlagen.",
): Promise<T> {
  const response = await fetch(url, init)
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw createApiError(errorMessage(payload, fallbackError), response.status)
  }
  return payload as T
}

export function jsonRequest(body: unknown, method = "POST"): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }
}
