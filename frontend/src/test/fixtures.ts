import type { AuthUser } from '../types/auth'

export const adminUser: AuthUser = {
  id: 1,
  email: 'admin@example.com',
  role: 'admin',
  is_active: true,
  status: 'active',
  created_at: '2026-10-01T10:00:00Z',
}

export const analystUser: AuthUser = {
  id: 2,
  email: 'analista@example.com',
  role: 'analyst',
  is_active: true,
  status: 'active',
  created_at: '2026-10-02T10:00:00Z',
}

export const pendingUser: AuthUser = {
  id: 3,
  email: 'pendiente@example.com',
  role: 'analyst',
  is_active: false,
  status: 'pending',
  created_at: '2026-10-03T10:00:00Z',
}

export const disabledUser: AuthUser = {
  id: 4,
  email: 'desactivada@example.com',
  role: 'analyst',
  is_active: false,
  status: 'disabled',
  created_at: '2026-10-04T10:00:00Z',
}
