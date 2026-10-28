// Validaciones del proceso principal sin dependencias de Electron, para poder probarlas de forma aislada.

export interface ApiResult {
  status: number
  body: unknown
}

export interface TrustedRenderer {
  // Servidor de desarrollo (electron-vite); si existe, es el único origen de confianza.
  devServerUrl?: string
  // index.html empaquetado, como URL file://.
  fileUrl: string
}

function parseUrl(value: string): URL | null {
  try {
    return new URL(value)
  } catch {
    return null
  }
}

function withoutQueryAndFragment(url: URL): string {
  return `${url.protocol}//${url.host}${url.pathname}`
}

/** Un emisor o destino de navegación es de confianza solo si es la propia interfaz de RESPIRA. */
export function isTrustedRendererUrl(candidate: string | undefined, trusted: TrustedRenderer): boolean {
  if (!candidate) return false
  const url = parseUrl(candidate)
  if (!url) return false

  if (trusted.devServerUrl) {
    const dev = parseUrl(trusted.devServerUrl)
    return dev !== null && url.origin === dev.origin
  }
  const file = parseUrl(trusted.fileUrl)
  return file !== null && url.protocol === 'file:' && withoutQueryAndFragment(url) === withoutQueryAndFragment(file)
}

/** Solo enlaces web explícitos pueden abrirse fuera de la aplicación (nunca file:, javascript: ni protocolos propios). */
export function isSafeExternalUrl(candidate: string): boolean {
  const url = parseUrl(candidate)
  return url !== null && (url.protocol === 'https:' || url.protocol === 'http:')
}

const SERVER_ERROR_MESSAGE = 'El servidor no pudo completar la solicitud.'
const VALIDATION_ERROR_MESSAGE = 'Los datos enviados no son válidos.'

/** Los cuerpos de error internos (5xx) y de validación (422, que puede reflejar la entrada) no llegan al renderer. */
export function sanitizeApiResult(result: ApiResult): ApiResult {
  if (result.status >= 500) return { status: result.status, body: { detail: SERVER_ERROR_MESSAGE } }
  if (result.status === 422) return { status: result.status, body: { detail: VALIDATION_ERROR_MESSAGE } }
  return result
}

export function readCredentials(value: unknown): { email: string; password: string } | null {
  if (typeof value !== 'object' || value === null) return null
  const { email, password } = value as Record<string, unknown>
  if (typeof email !== 'string' || typeof password !== 'string') return null
  if (email.length === 0 || email.length > 254 || password.length === 0 || password.length > 128) return null
  return { email, password }
}

/** Única operación administrativa permitida desde el renderer: activar o desactivar una cuenta. */
export function parseSetActiveArgs(userId: unknown, isActive: unknown): { userId: number; isActive: boolean } | null {
  if (typeof userId !== 'number' || !Number.isSafeInteger(userId) || userId < 1) return null
  if (typeof isActive !== 'boolean') return null
  return { userId, isActive }
}
