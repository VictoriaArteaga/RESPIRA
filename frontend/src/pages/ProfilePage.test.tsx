import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../context/AuthContext'
import { adminUser, analystUser } from '../test/fixtures'
import { ProfilePage } from './ProfilePage'

vi.mock('../context/AuthContext')

function signInAs(user: typeof adminUser | null) {
  vi.mocked(useAuth).mockReturnValue({
    user,
    status: user ? 'authenticated' : 'anonymous',
  } as unknown as ReturnType<typeof useAuth>)
}

describe('ProfilePage', () => {
  beforeEach(() => vi.resetAllMocks())

  it('muestra los datos del perfil y los permisos de administración', () => {
    signInAs(adminUser)
    render(<ProfilePage />)

    expect(screen.getByRole('heading', { name: 'Mi perfil' })).toBeInTheDocument()
    expect(screen.getAllByText('admin@example.com').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Administrador').length).toBeGreaterThan(0)
    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText('Aprobar, desactivar y reactivar cuentas de usuario.')).toBeInTheDocument()
  })

  it('no ofrece permisos de administración a un analista', () => {
    signInAs(analystUser)
    render(<ProfilePage />)

    expect(screen.getAllByText('Analista').length).toBeGreaterThan(0)
    expect(screen.queryByText('Aprobar, desactivar y reactivar cuentas de usuario.')).not.toBeInTheDocument()
    expect(screen.getByText('La administración de usuarios no está disponible para tu rol.')).toBeInTheDocument()
  })

  it('indica que no hay información cuando no hay sesión', () => {
    signInAs(null)
    render(<ProfilePage />)

    expect(screen.getByText('No hay información de perfil disponible.')).toBeInTheDocument()
  })
})
