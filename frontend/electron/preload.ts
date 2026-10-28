import { contextBridge, ipcRenderer } from 'electron'

interface DesktopApiResponse {
  status: number
  body: unknown
}

function isDesktopApiResponse(value: unknown): value is DesktopApiResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    typeof value.status === 'number' &&
    'body' in value
  )
}

async function invoke(channel: string, ...args: unknown[]): Promise<DesktopApiResponse> {
  const response: unknown = await ipcRenderer.invoke(channel, ...args)
  if (!isDesktopApiResponse(response)) {
    throw new Error('The desktop API bridge returned an invalid response.')
  }
  return response
}

interface Credentials {
  email: string
  password: string
}

contextBridge.exposeInMainWorld('respiraDesktop', {
  platform: process.platform,
  getApi: (path: string) => invoke('respira:api-get', path),
  auth: {
    register: (credentials: Credentials) => invoke('respira:auth-register', credentials),
    login: (credentials: Credentials) => invoke('respira:auth-login', credentials),
    session: () => invoke('respira:auth-session'),
    logout: () => invoke('respira:auth-logout'),
  },
  admin: {
    listUsers: () => invoke('respira:admin-users-list'),
    setUserActive: (userId: number, isActive: boolean) => invoke('respira:admin-users-set-active', userId, isActive),
  },
})
