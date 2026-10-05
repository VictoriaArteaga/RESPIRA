import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { join } from 'node:path'

const apiBaseUrl = __RESPIRA_API_URL__.replace(/\/+$/, '')
const municipalityDetailPath = /^\/api\/municipalities\/\d+$/
const allowedPaths = new Set(['/api/dashboard', '/api/municipalities', '/api/cases'])
const allowedCaseFilters = new Set(['municipality_id', 'year', 'epidemiological_week'])

function isAllowedApiPath(path: string): boolean {
  let url: URL
  try {
    url = new URL(path, apiBaseUrl)
  } catch {
    return false
  }

  if (url.origin !== new URL(apiBaseUrl).origin) return false
  if (!allowedPaths.has(url.pathname) && !municipalityDetailPath.test(url.pathname)) return false
  if (url.pathname !== '/api/cases') return url.search.length === 0

  return [...url.searchParams].every(
    ([key, value]) => allowedCaseFilters.has(key) && /^\d+$/.test(value),
  )
}

ipcMain.handle('respira:api-get', async (_event, path: unknown) => {
  if (typeof path !== 'string' || !isAllowedApiPath(path)) {
    return { status: 400, body: { detail: 'API route is not allowed.' } }
  }

  let response: Response
  try {
    response = await fetch(new URL(path, apiBaseUrl), {
      headers: { Accept: 'application/json' },
    })
  } catch (error) {
    if (error instanceof TypeError) {
      return { status: 0, body: { detail: 'Unable to connect to the RESPIRA API.' } }
    }
    throw error
  }

  return { status: response.status, body: await response.json() as unknown }
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
    void shell.openExternal(url)
    return { action: 'deny' }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    void window.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    void window.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
