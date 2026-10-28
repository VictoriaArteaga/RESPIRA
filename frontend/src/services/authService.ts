import type { AuthUser, Credentials } from '../types/auth'
import { ApiError, getApiBaseUrl, setBrowserToken } from './api'

interface RawResponse {
  status: number
  body: unknown
}

type AuthAction = 'register' | 'login' | 'session' | 'logout'

const CONNECTION_ERROR = 'No fue posible conectar con el servidor.'

// Solo para ejecución en navegador (desarrollo): el token queda en memoria y se pierde al recargar.
let browserToken: string | null = null

function detailOf(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  return typeof detail === 'string' ? detail : fallback
}

async function browserRequest(method: 'GET' | 'POST', path: string, payload?: Credentials): Promise<RawResponse> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (payload) headers['Content-Type'] = 'application/json'
  if (browserToken) headers.Authorization = `Bearer ${browserToken}`

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    headers,
    body: payload ? JSON.stringify(payload) : undefined,
  })
  const text = await response.text()
  return { status: response.status, body: text ? (JSON.parse(text) as unknown) : null }
}

async function browserCall(action: AuthAction, credentials?: Credentials): Promise<RawResponse> {
  if (action === 'register') return browserRequest('POST', '/api/auth/register', credentials)
  if (action === 'session') {
    return browserToken ? browserRequest('GET', '/api/auth/me') : { status: 401, body: null }
  }
  if (action === 'logout') {
    const result = browserToken ? await browserRequest('POST', '/api/auth/logout') : { status: 204, body: null }
    browserToken = null
    setBrowserToken(null)
    return result
  }

  const login = await browserRequest('POST', '/api/auth/login', credentials)
  const token = (login.body as { access_token?: unknown } | null)?.access_token
  if (login.status !== 200 || typeof token !== 'string') return login
  browserToken = token
  setBrowserToken(token)
  return browserRequest('GET', '/api/auth/me')
}

async function call(action: AuthAction, credentials?: Credentials): Promise<RawResponse> {
  try {
    if (window.respiraDesktop) {
      return await window.respiraDesktop.auth[action](credentials as Credentials)
    }
    return await browserCall(action, credentials)
  } catch {
    return { status: 0, body: null }
  }
}

function ensureOk(response: RawResponse, validationMessage: string): void {
  if (response.status === 0) throw new ApiError(CONNECTION_ERROR, 0)
  if (response.status >= 200 && response.status < 300) return
  if (response.status === 400 || response.status === 422) throw new ApiError(validationMessage, response.status)
  throw new ApiError(detailOf(response.body, 'No fue posible completar la operación.'), response.status)
}

export async function register(credentials: Credentials): Promise<void> {
  ensureOk(await call('register', credentials), 'Los datos de registro no son válidos.')
}

export async function login(credentials: Credentials): Promise<AuthUser> {
  const response = await call('login', credentials)
  ensureOk(response, 'Los datos de inicio de sesión no son válidos.')
  return response.body as AuthUser
}

export async function restoreSession(): Promise<AuthUser | null> {
  const response = await call('session')
  return response.status === 200 ? (response.body as AuthUser) : null
}

export async function logout(): Promise<void> {
  await call('logout')
}
