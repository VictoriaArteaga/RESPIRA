interface Window {
  respiraDesktop?: {
    platform: string
    getApi: (path: string) => Promise<{
      status: number
      body: unknown
    }>
  }
}
