import { app, BrowserWindow, ipcMain, safeStorage, shell, type IpcMainInvokeEvent } from 'electron'
import { existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import {
  isSafeExternalUrl,
  isTrustedRendererUrl,
  parseSetActiveArgs,
  readCredentials,
  sanitizeApiResult,
  type ApiResult,
  type TrustedRenderer,
} from './security'

const apiBaseUrl = __RESPIRA_API_URL__.replace(/\/+$/, '')
const municipalityDetailPath = /^\/api\/municipalities\/\d+$/
const allowedPaths = new Set(['/api/dashboard', '/api/municipalities', '/api/cases', '/api/risk-map'])
const allowedCaseFilters = new Set(['municipality_id', 'year', 'epidemiological_week'])
const allowedRiskFilters = new Set(['year', 'week'])
const municipalityAnalysisPath = /^\/api\/municipalities\/\d+\/(?:risk|endemic-channel)$/

function isAllowedApiPath(path: string): boolean {
  let url: URL
  try {
    url = new URL(path, apiBaseUrl)
  } catch {
    return false
  }

  if (url.origin !== new URL(apiBaseUrl).origin) return false
  if (!allowedPaths.has(url.pathname) && !municipalityDetailPath.test(url.pathname) && !municipalityAnalysisPath.test(url.pathname)) return false
  if (url.pathname === '/api/risk-map') return [...url.searchParams].every(([key, value]) => allowedRiskFilters.has(key) && /^\d+$/.test(value))
  if (municipalityAnalysisPath.test(url.pathname)) return [...url.searchParams].every(([key, value]) => key === 'year' && /^\d+$/.test(value))
  if (url.pathname !== '/api/cases') return url.search.length === 0

  return [...url.searchParams].every(([key, value]) => allowedCaseFilters.has(key) && /^\d+$/.test(value))
}

const getTrustedRenderer = (): TrustedRenderer => ({
  devServerUrl: process.env.ELECTRON_RENDERER_URL,
  fileUrl: pathToFileURL(join(__dirname, '../renderer/index.html')).href,
})

// Todos los canales IPC exigen que el emisor sea el marco principal de la interfaz de RESPIRA.
function secureHandle(
  channel: string,
  handler: (event: IpcMainInvokeEvent, ...args: unknown[]) => Promise<ApiResult> | ApiResult,
): void {
  ipcMain.handle(channel, (event, ...args: unknown[]): Promise<ApiResult> | ApiResult => {
    const frame = event.senderFrame
    if (!frame || frame.parent !== null || !isTrustedRendererUrl(frame.url, getTrustedRenderer())) {
      return { status: 403, body: { detail: 'Remitente no autorizado.' } }
    }
    return handler(event, ...args)
  })
}

// El token vive solo en el proceso principal: el renderer nunca lo recibe ni puede leerlo.
let accessToken: string | null = null
const sessionFile = () => join(app.getPath('userData'), 'session.bin')

function persistToken(token: string): void {
  // Si el sistema no ofrece cifrado (p. ej. Linux sin keyring), la sesión solo se mantiene en memoria.
  if (!safeStorage.isEncryptionAvailable()) return
  writeFileSync(sessionFile(), safeStorage.encryptString(token), { mode: 0o600 })
}

function clearToken(): void {
  accessToken = null
  if (existsSync(sessionFile())) rmSync(sessionFile())
}

function restoreToken(): void {
  if (!safeStorage.isEncryptionAvailable() || !existsSync(sessionFile())) return
  try {
    accessToken = safeStorage.decryptString(readFileSync(sessionFile()))
  } catch {
    clearToken()
  }
}

async function apiRequest(method: 'GET' | 'POST' | 'PATCH', path: string, payload?: unknown): Promise<ApiResult> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (payload !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response: Response
  try {
    response = await fetch(new URL(path, apiBaseUrl), {
      method,
      headers,
      body: payload === undefined ? undefined : JSON.stringify(payload),
    })
  } catch (error) {
    if (error instanceof TypeError) {
      return { status: 0, body: { detail: 'Unable to connect to the RESPIRA API.' } }
    }
    throw error
  }

  // Un 401 con token enviado significa sesión caducada o revocada: se descarta el token local.
  if (response.status === 401 && accessToken) clearToken()
  const text = await response.text()
  let body: unknown = null
  try {
    body = text ? (JSON.parse(text) as unknown) : null
  } catch {
    body = null
  }
  return sanitizeApiResult({ status: response.status, body })
}

secureHandle('respira:api-get', async (_event, path: unknown) => {
  if (typeof path !== 'string' || !isAllowedApiPath(path)) {
    return { status: 400, body: { detail: 'API route is not allowed.' } }
  }
  return apiRequest('GET', path)
})

secureHandle('respira:auth-register', async (_event, value: unknown): Promise<ApiResult> => {
  const credentials = readCredentials(value)
  if (!credentials) return { status: 400, body: { detail: 'Datos de registro no válidos.' } }
  return apiRequest('POST', '/api/auth/register', credentials)
})

secureHandle('respira:auth-login', async (_event, value: unknown): Promise<ApiResult> => {
  const credentials = readCredentials(value)
  if (!credentials) return { status: 400, body: { detail: 'Datos de inicio de sesión no válidos.' } }

  const login = await apiRequest('POST', '/api/auth/login', credentials)
  const token = (login.body as { access_token?: unknown } | null)?.access_token
  if (login.status !== 200 || typeof token !== 'string') return { status: login.status, body: login.body }

  accessToken = token
  persistToken(token)
  return apiRequest('GET', '/api/auth/me')
})

secureHandle('respira:auth-session', async (): Promise<ApiResult> => {
  if (!accessToken) return { status: 401, body: null }
  return apiRequest('GET', '/api/auth/me')
})

secureHandle('respira:auth-logout', async (): Promise<ApiResult> => {
  // La revocación en el servidor es lo que invalida el token; el borrado local se hace aunque falle la red.
  const result = accessToken ? await apiRequest('POST', '/api/auth/logout') : { status: 204, body: null }
  clearToken()
  return result
})

// Administración de usuarios: el renderer solo puede listar y activar/desactivar; roles y creación no se exponen.
secureHandle('respira:admin-users-list', (): Promise<ApiResult> => apiRequest('GET', '/api/admin/users'))

secureHandle('respira:admin-users-set-active', (_event, userId: unknown, isActive: unknown): Promise<ApiResult> | ApiResult => {
  const args = parseSetActiveArgs(userId, isActive)
  if (!args) return { status: 400, body: { detail: 'Datos de administración no válidos.' } }
  return apiRequest('PATCH', `/api/admin/users/${args.userId}`, { is_active: args.isActive })
})

function createWindow(): void {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: '#F8FAFC',
    show: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  window.once('ready-to-show', () => window.show())
  window.webContents.setWindowOpenHandler(({ url }) => {
    if (isSafeExternalUrl(url)) void shell.openExternal(url)
    return { action: 'deny' }
  })
  // La ventana nunca sale de la interfaz de RESPIRA: otras navegaciones se bloquean y los enlaces web se abren fuera.
  const guardNavigation = (event: { preventDefault: () => void }, url: string): void => {
    if (isTrustedRendererUrl(url, getTrustedRenderer())) return
    event.preventDefault()
    if (isSafeExternalUrl(url)) void shell.openExternal(url)
  }
  window.webContents.on('will-navigate', guardNavigation)
  window.webContents.on('will-redirect', guardNavigation)

  if (process.env.ELECTRON_RENDERER_URL) {
    void window.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    void window.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  restoreToken()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
