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

export async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
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
        headers: { Accept: 'application/json' },
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
  if (status < 200 || status >= 300) {
    throw new ApiError(`El servidor respondió con el estado ${status}.`, status)
  }

  return body as T
}

export function getApiBaseUrl(): string {
  return apiBaseUrl
}
