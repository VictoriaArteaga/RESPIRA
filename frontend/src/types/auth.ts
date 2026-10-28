export type UserRole = 'admin' | 'analyst'

export type AccountStatus = 'pending' | 'active' | 'disabled'

export interface AuthUser {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  status: AccountStatus
  created_at: string
}

export interface Credentials {
  email: string
  password: string
}
