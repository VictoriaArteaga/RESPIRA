import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../i18n/I18nContext'
import { ThemeProvider } from '../theme/ThemeContext'
import { SettingsPage } from './SettingsPage'

function renderSettings() {
  return render(
    <ThemeProvider>
      <I18nProvider>
        <SettingsPage />
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

describe('SettingsPage: idioma y apariencia', () => {
  beforeEach(() => {
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
})
