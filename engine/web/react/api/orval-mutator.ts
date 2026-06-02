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

export function toApiError(error: unknown, fallbackError = "Anfrage fehlgeschlagen."): ApiError {
  const payload = error && typeof error === "object" ? error : {}
  const statusValue = (payload as { status?: unknown }).status
  const status = typeof statusValue === "number" ? statusValue : undefined
  return createApiError(errorMessage(payload, fallbackError), status)
}

export async function orvalFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, options)

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw toApiError(payload, "Anfrage fehlgeschlagen.")
  }

  if (url.includes("/api/chat/stream")) {
    return {
      data: response.body,
      status: response.status,
      headers: response.headers,
    } as T
  }

  if (response.status === 204) {
    return {
      data: {},
      status: response.status,
      headers: response.headers,
    } as T
  }

  return {
    data: await response.json().catch(() => ({})),
    status: response.status,
    headers: response.headers,
  } as T
}

export async function orvalFetchStream<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw toApiError(payload, "Anfrage fehlgeschlagen.")
  }
  return {
    data: response.body,
    status: response.status,
    headers: response.headers,
  } as T
}
