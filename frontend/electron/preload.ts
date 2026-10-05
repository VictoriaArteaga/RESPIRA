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

contextBridge.exposeInMainWorld('respiraDesktop', {
  platform: process.platform,
  async getApi(path: string): Promise<DesktopApiResponse> {
    const response: unknown = await ipcRenderer.invoke('respira:api-get', path)
    if (!isDesktopApiResponse(response)) {
      throw new Error('The desktop API bridge returned an invalid response.')
    }
    return response
  },
})
