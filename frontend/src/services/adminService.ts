import type { AuthUser } from '../types/auth'
import { ApiError, UNAUTHORIZED_EVENT } from './api'
import { browserRequest, type RawResponse } from './authService'

const CONNECTION_ERROR = 'No fue posible conectar con el servidor.'

async function call(action: 'list' | 'setActive', userId = 0, isActive = false): Promise<RawResponse> {
  try {
    if (window.respiraDesktop) {
      const { admin } = window.respiraDesktop
      return action === 'list' ? await admin.listUsers() : await admin.setUserActive(userId, isActive)
    }
    // Respaldo para navegador (solo desarrollo): usa el token en memoria de authService.
    return action === 'list'
      ? await browserRequest('GET', '/api/admin/users')
      : await browserRequest('PATCH', `/api/admin/users/${userId}`, { is_active: isActive })
  } catch {
    return { status: 0, body: null }
  }
}

function toError(response: RawResponse): ApiError {
  const { status } = response
  if (status === 0) return new ApiError(CONNECTION_ERROR, 0)
  if (status === 401) {
    // El proceso principal ya descartó el token; se avisa al renderer para volver al inicio de sesión.
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    return new ApiError('Tu sesión expiró. Inicia sesión de nuevo.', status)
  }
  if (status === 403) return new ApiError('No tienes permisos de administrador para esta acción.', status)
  if (status === 404) return new ApiError('La cuenta ya no existe. Actualiza el listado.', status)
  if (status === 400) return new ApiError('No puedes modificar tu propia cuenta.', status)
  if (status === 429) return new ApiError('Demasiados intentos. Inténtalo de nuevo más tarde.', status)
  return new ApiError('No fue posible completar la operación.', status)
}

export async function listUsers(): Promise<AuthUser[]> {
  const response = await call('list')
  if (response.status !== 200 || !Array.isArray(response.body)) throw toError(response)
  return response.body as AuthUser[]
}

export async function setUserActive(userId: number, isActive: boolean): Promise<AuthUser> {
  const response = await call('setActive', userId, isActive)
  if (response.status !== 200) throw toError(response)
  return response.body as AuthUser
}
