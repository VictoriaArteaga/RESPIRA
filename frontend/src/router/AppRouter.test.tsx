import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/authService'
import { adminUser, analystUser } from '../test/fixtures'
import { AppRouter } from './AppRouter'

vi.mock('../services/authService')
vi.mock('../services/adminService')

// Las páginas epidemiológicas dependen de mapas y gráficas; aquí solo importa el control de acceso.
vi.mock('../pages/AdminUsersPage', () => ({ AdminUsersPage: () => <h1>Vista de administración</h1> }))
vi.mock('../pages/DashboardPage', () => ({ DashboardPage: () => <h1>Vista del dashboard</h1> }))
vi.mock('../pages/AlertsPage', () => ({ AlertsPage: () => null }))
vi.mock('../pages/CasesPage', () => ({ CasesPage: () => null }))
vi.mock('../pages/MunicipalitiesPage', () => ({ MunicipalitiesPage: () => null }))
vi.mock('../pages/MunicipalityDetailPage', () => ({ MunicipalityDetailPage: () => null }))
vi.mock('../pages/RiskMapPage', () => ({ RiskMapPage: () => null }))
vi.mock('../pages/EndemicPage', () => ({ EndemicPage: () => null }))
vi.mock('../pages/SettingsPage', () => ({ SettingsPage: () => null }))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </MemoryRouter>,
  )
}

const ADMIN_LINK = { name: 'Administración de usuarios' }

describe('control de acceso a la administración de usuarios', () => {
  beforeEach(() => {
    vi.mocked(authService.restoreSession).mockResolvedValue(adminUser)
  })

  it('el administrador accede a la vista y ve la opción de navegación', async () => {
    renderAt('/admin/users')

    expect(await screen.findByRole('heading', { name: 'Vista de administración' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', ADMIN_LINK).length).toBeGreaterThan(0)
  })

  it('el analista no ve la opción de administración', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(analystUser)

    renderAt('/dashboard')

    expect(await screen.findByRole('heading', { name: 'Vista del dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('link', ADMIN_LINK)).not.toBeInTheDocument()
  })

  it('el acceso directo del analista a la ruta administrativa se redirige', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(analystUser)

    renderAt('/admin/users')

    expect(await screen.findByRole('heading', { name: 'Vista del dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Vista de administración' })).not.toBeInTheDocument()
  })

  it('sin sesión la ruta administrativa lleva al inicio de sesión', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(null)

    renderAt('/admin/users')

    expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Vista de administración' })).not.toBeInTheDocument()
  })
})
