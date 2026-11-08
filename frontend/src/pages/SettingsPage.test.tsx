import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuth } from '../context/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { PreferencesProvider } from '../preferences/PreferencesContext'
import { adminUser } from '../test/fixtures'
import { ThemeProvider } from '../theme/ThemeContext'
import { SettingsPage } from './SettingsPage'

function renderSettings() {
  return render(
    <ThemeProvider>
      <I18nProvider>
        <PreferencesProvider>
          <SettingsPage />
        </PreferencesProvider>
      </I18nProvider>
    </ThemeProvider>,
  )
}

// Almacenamiento en memoria: el entorno de pruebas no siempre expone localStorage.
function memoryStorage(): Storage {
  const data = new Map<string, string>()
  return {
    get length() {
      return data.size
    },
    clear: () => data.clear(),
    getItem: (key) => data.get(key) ?? null,
    key: (index) => [...data.keys()][index] ?? null,
    removeItem: (key) => void data.delete(key),
    setItem: (key, value) => void data.set(key, value),
  }
}

vi.mock('../context/AuthContext')

describe('SettingsPage: idioma y apariencia', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ user: adminUser, status: 'authenticated' } as unknown as ReturnType<
      typeof useAuth
    >)
    vi.stubGlobal('localStorage', memoryStorage())
    window.localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  afterEach(() => {
    window.localStorage.clear()
    document.documentElement.classList.remove('dark')
    document.documentElement.lang = 'es'
    vi.unstubAllGlobals()
  })

  it('cambia la interfaz a inglés y recuerda la preferencia', async () => {
    renderSettings()
    expect(screen.getByRole('heading', { name: 'Configuración' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'English' }))

    expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
    expect(window.localStorage.getItem('respira.language')).toBe('en')
  })

  it('activa y desactiva el modo oscuro', async () => {
    renderSettings()

    await userEvent.click(screen.getByRole('radio', { name: 'Oscuro' }))
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(window.localStorage.getItem('respira.theme')).toBe('dark')

    await userEvent.click(screen.getByRole('radio', { name: 'Claro' }))
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('aplica y recuerda el tamaño de texto, la densidad y las animaciones', async () => {
    renderSettings()

    await userEvent.click(screen.getByRole('radio', { name: 'Grande' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Compacta' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Reducidas' }))

    expect(document.documentElement.dataset.text).toBe('large')
    expect(document.documentElement.dataset.density).toBe('compact')
    expect(document.documentElement.dataset.motion).toBe('reduced')
    expect(JSON.parse(window.localStorage.getItem('respira.preferences') ?? '{}')).toMatchObject({
      textSize: 'large',
      density: 'compact',
      reduceMotion: true,
    })
  })

  it('guarda la página de inicio elegida', async () => {
    renderSettings()

    await userEvent.selectOptions(screen.getByLabelText('Vista inicial'), '/alerts')

    expect(JSON.parse(window.localStorage.getItem('respira.preferences') ?? '{}').startPage).toBe('/alerts')
  })

  it('restablece las preferencias a sus valores predeterminados', async () => {
    renderSettings()

    await userEvent.click(screen.getByRole('radio', { name: 'Grande' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Oscuro' }))
    await userEvent.click(screen.getByRole('button', { name: 'Restablecer' }))

    expect(document.documentElement.dataset.text).toBe('normal')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(screen.getByRole('status')).toHaveTextContent('Preferencias restablecidas.')
  })
})
