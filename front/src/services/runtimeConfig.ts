export const DEFAULT_BACKEND_URL = 'http://localhost:8011'

declare global {
  interface Window {
    __ENV?: {
      BACKEND_URL?: string
    }
  }
}

function normalizeUrl(value?: string | null): string | undefined {
  const trimmed = value?.trim()
  if (!trimmed) return undefined
  return trimmed.replace(/\/+$/, '')
}

export function getBackendBaseUrl(): string {
  return (
    normalizeUrl(window.__ENV?.BACKEND_URL) ??
    normalizeUrl(import.meta.env.VITE_BACKEND_URL) ??
    DEFAULT_BACKEND_URL
  )
}

export function getApiBaseUrl(): string {
  return normalizeUrl(import.meta.env.VITE_API_BASE_URL) ?? `${getBackendBaseUrl()}/api`
}
