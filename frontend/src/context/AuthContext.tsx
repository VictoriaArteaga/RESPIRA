import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { UNAUTHORIZED_EVENT } from '../services/api'
import * as authService from '../services/authService'
import type { AuthUser, Credentials } from '../types/auth'

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface AuthContextValue {
  status: AuthStatus
  user: AuthUser | null
  login: (credentials: Credentials) => Promise<void>
  register: (credentials: Credentials) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    let active = true
    void authService.restoreSession().then((restored) => {
      if (!active) return
      setUser(restored)
      setStatus(restored ? 'authenticated' : 'anonymous')
    })
    return () => {
      active = false
    }
  }, [])

  // Una respuesta 401 de la API (sesión caducada o revocada) devuelve al usuario al inicio de sesión.
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setStatus('anonymous')
    }
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
  }, [])

  const login = useCallback(async (credentials: Credentials) => {
    const authenticated = await authService.login(credentials)
    setUser(authenticated)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(async () => {
    await authService.logout()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, login, register: authService.register, logout }),
    [status, user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider.')
  return context
}
