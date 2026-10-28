export type UserRole = 'admin' | 'analyst'

export interface AuthUser {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface Credentials {
  email: string
  password: string
}
