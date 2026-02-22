import type { ApiEnvelope } from './contracts'

type RequestMethod = 'GET' | 'POST' | 'PATCH'

type RequestOptions = {
  method?: RequestMethod
  body?: unknown
}

function resolveBearerToken(): string {
  return window.localStorage.getItem('platform_token') ?? ''
}

export async function apiRequest<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(url, {
    method: options.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(resolveBearerToken() ? { Authorization: `Bearer ${resolveBearerToken()}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  const payload = (await response.json()) as ApiEnvelope<T> | { error?: { message?: string } }
  if (!response.ok || !('data' in payload)) {
    const errorPayload = payload as { error?: { message?: string } }
    throw new Error(errorPayload.error?.message ?? `Request failed: ${response.status}`)
  }

  return payload.data
}
