import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type { UserRole } from '../../types/auth'
import { Loading } from '../common/Loading'

interface ProtectedRouteProps extends PropsWithChildren {
  roles?: UserRole[]
}

// La autorización real se aplica en el servidor; esta protección solo evita mostrar vistas sin permiso.
export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { status, user } = useAuth()

  if (status === 'loading') return <Loading />
  if (status === 'anonymous' || !user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
