import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HashRouter, MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { PreferencesProvider } from '../preferences/PreferencesContext'
import { AppRouter } from '../router/AppRouter'
import * as authService from '../services/authService'
import { analystUser } from '../test/fixtures'

vi.mock('../services/authService')
vi.mock('../services/adminService')
vi.mock('./DashboardPage', () => ({ DashboardPage: () => <h1>Vista del dashboard</h1> }))
vi.mock('./AlertsPage', () => ({ AlertsPage: () => null }))
vi.mock('./CasesPage', () => ({ CasesPage: () => null }))
vi.mock('./MunicipalitiesPage', () => ({ MunicipalitiesPage: () => null }))
vi.mock('./MunicipalityDetailPage', () => ({ MunicipalityDetailPage: () => null }))
vi.mock('./RiskMapPage', () => ({ RiskMapPage: () => null }))
vi.mock('./EndemicPage', () => ({ EndemicPage: () => null }))
vi.mock('./SettingsPage', () => ({ SettingsPage: () => null }))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <PreferencesProvider>
          <AppRouter />
        </PreferencesProvider>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('pantalla de inicio', () => {
  it('sin sesión muestra la información de RESPIRA y los accesos a inicio de sesión y registro', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(null)

    renderAt('/')

    expect(await screen.findByRole('heading', { level: 1, name: /alerta temprana/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '¿Qué es RESPIRA?' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Iniciar sesión' })[0]).toHaveAttribute('href', '/login')
    expect(screen.getAllByRole('link', { name: 'Solicitar cuenta' })[0]).toHaveAttribute('href', '/register')
  })

  it('los botones del menú llevan a su apartado de la pantalla de inicio y no al inicio de sesión', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(null)
    // La aplicación usa HashRouter: un enlace "#apartado" se leería como una ruta y mandaría al inicio de sesión.
    window.location.hash = '#/'
    const scrolled: string[] = []
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      value(this: Element) {
        scrolled.push(this.id)
      },
    })
    render(
      <HashRouter>
        <AuthProvider>
          <PreferencesProvider>
            <AppRouter />
          </PreferencesProvider>
        </AuthProvider>
      </HashRouter>,
    )
    await screen.findByRole('heading', { level: 1, name: /alerta temprana/i })

    for (const [label, section] of [
      ['¿Qué es?', 'que-es'],
      ['Funciones', 'funciones'],
      ['Niveles', 'niveles'],
    ] as const) {
      await userEvent.click(screen.getByText(label))
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 60)) // da tiempo a que el router reaccione si cambiara la ruta
      })
      expect(scrolled.at(-1)).toBe(section)
      expect(window.location.hash).toBe('#/')
      expect(screen.getByRole('heading', { level: 1, name: /alerta temprana/i })).toBeInTheDocument()
      expect(screen.queryByRole('heading', { name: 'Bienvenido' })).not.toBeInTheDocument()
    }
    // Los accesos de sesión y registro siguen siendo enlaces a sus páginas.
    expect(screen.getAllByRole('link', { name: 'Iniciar sesión' })[0]).toHaveAttribute('href', '#/login')
    expect(screen.getAllByRole('link', { name: 'Solicitar cuenta' })[0]).toHaveAttribute('href', '#/register')
  })

  it('con sesión activa redirige a la página de inicio elegida', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(analystUser)

    renderAt('/')

    expect(await screen.findByRole('heading', { name: 'Vista del dashboard' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '¿Qué es RESPIRA?' })).not.toBeInTheDocument()
  })

  it('inicio de sesión y registro ofrecen volver a la pantalla de inicio', async () => {
    vi.mocked(authService.restoreSession).mockResolvedValue(null)

    const { unmount } = renderAt('/login')
    expect(await screen.findByRole('link', { name: 'Volver al inicio' })).toHaveAttribute('href', '/')
    unmount()

    renderAt('/register')
    expect(await screen.findByRole('link', { name: 'Volver al inicio' })).toHaveAttribute('href', '/')
  })
})
