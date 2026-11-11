const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export const UNAUTHORIZED_EVENT = 'respira:unauthorized'

// Solo para ejecución en navegador (desarrollo). En Electron el token permanece en el proceso principal.
let browserToken: string | null = null

export function setBrowserToken(token: string | null): void {
  browserToken = token
}

/** True cuando la interfaz usa datos de demostración locales en lugar del servidor (VITE_DEMO_DATA=true). */
export const isDemoData = import.meta.env.VITE_DEMO_DATA === 'true'

// Copia en memoria de las consultas de datos: al volver a una pantalla se muestra al instante. Los datos cambian
// muy rara vez, así que 2 minutos de vida bastan; se vacía al cerrar sesión o si el servidor responde 401.
const CACHE_TTL_MS = 2 * 60 * 1000
const CACHEABLE = /^\/api\/(?:dashboard|municipalities|cases|risk-map|alerts|forecast)(?:[/?]|$)/
const responseCache = new Map<string, { time: number; value: unknown }>()
window.addEventListener(UNAUTHORIZED_EVENT, () => responseCache.clear())

export function clearApiCache(): void {
  responseCache.clear()
}

export async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const cached = responseCache.get(path)
  if (cached && Date.now() - cached.time < CACHE_TTL_MS) return cached.value as T
  const value = await request<T>(path, signal)
  if (CACHEABLE.test(path)) responseCache.set(path, { time: Date.now(), value })
  return value
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  if (isDemoData) {
    const { resolveDemo } = await import('../mocks/demoApi')
    const demo = resolveDemo(path)
    if (demo !== undefined) return demo as T
  }
  let status: number
  let body: unknown
  try {
    if (window.respiraDesktop) {
      // Electron consulta desde el proceso principal para no depender del origen local ni de CORS.
      const response = await window.respiraDesktop.getApi(path)
      status = response.status
      body = response.body
    } else {
      const response = await fetch(`${apiBaseUrl}${path}`, {
        headers: {
          Accept: 'application/json',
          ...(browserToken ? { Authorization: `Bearer ${browserToken}` } : {}),
        },
        signal,
      })
      status = response.status
      body = await response.json()
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new ApiError('No fue posible conectar con el servidor.', 0)
  }

  if (status === 0) throw new ApiError('No fue posible conectar con el servidor.', 0)
  if (status === 401) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  if (status < 200 || status >= 300) {
    throw new ApiError(`El servidor respondió con el estado ${status}.`, status)
  }

  return body as T
}

export function getApiBaseUrl(): string {
  return apiBaseUrl
}
