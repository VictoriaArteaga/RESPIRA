interface DesktopApiResponse {
  status: number
  body: unknown
}

interface Window {
  respiraDesktop?: {
    platform: string
    getApi: (path: string) => Promise<DesktopApiResponse>
    auth: {
      register: (credentials: { email: string; password: string }) => Promise<DesktopApiResponse>
      login: (credentials: { email: string; password: string }) => Promise<DesktopApiResponse>
      session: () => Promise<DesktopApiResponse>
      logout: () => Promise<DesktopApiResponse>
    }
    admin: {
      listUsers: () => Promise<DesktopApiResponse>
      setUserActive: (userId: number, isActive: boolean) => Promise<DesktopApiResponse>
    }
  }
}
