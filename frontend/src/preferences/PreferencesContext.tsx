import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'

export type TextSize = 'normal' | 'large'
export type Density = 'comfortable' | 'compact'

/** Vistas que pueden abrirse al iniciar sesión. */
export const START_PAGES = ['/dashboard', '/municipalities', '/risk-map', '/endemic', '/cases', '/alerts'] as const
export type StartPage = (typeof START_PAGES)[number]

export interface Preferences {
  textSize: TextSize
  density: Density
  reduceMotion: boolean
  startPage: StartPage
}

export const DEFAULT_PREFERENCES: Preferences = {
  textSize: 'normal',
  density: 'comfortable',
  reduceMotion: false,
  startPage: '/dashboard',
}

interface PreferencesValue extends Preferences {
  setPreference: <K extends keyof Preferences>(key: K, value: Preferences[K]) => void
  reset: () => void
}

const STORAGE_KEY = 'respira.preferences'

function load(): Preferences {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_PREFERENCES
    const parsed = JSON.parse(raw) as Partial<Preferences>
    return {
      textSize: parsed.textSize === 'large' ? 'large' : 'normal',
      density: parsed.density === 'compact' ? 'compact' : 'comfortable',
      reduceMotion: parsed.reduceMotion === true,
      startPage: START_PAGES.includes(parsed.startPage as StartPage)
        ? (parsed.startPage as StartPage)
        : DEFAULT_PREFERENCES.startPage,
    }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

function save(preferences: Preferences) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
  } catch {
    // Sin almacenamiento disponible: las preferencias solo duran la sesión.
  }
}

// Valor por defecto para que los componentes funcionen también fuera del proveedor, p. ej. en pruebas.
const PreferencesContext = createContext<PreferencesValue>({
  ...DEFAULT_PREFERENCES,
  setPreference: () => undefined,
  reset: () => undefined,
})

export function PreferencesProvider({ children }: PropsWithChildren) {
  const [preferences, setPreferences] = useState<Preferences>(load)

  // Los atributos de <html> activan las reglas de index.css (tamaño de texto, densidad y animaciones).
  useLayoutEffect(() => {
    const root = document.documentElement
    root.dataset.text = preferences.textSize
    root.dataset.density = preferences.density
    root.dataset.motion = preferences.reduceMotion ? 'reduced' : 'full'
  }, [preferences])

  const setPreference = useCallback<PreferencesValue['setPreference']>((key, value) => {
    setPreferences((current) => {
      const next = { ...current, [key]: value }
      save(next)
      return next
    })
  }, [])

  const reset = useCallback(() => {
    setPreferences(DEFAULT_PREFERENCES)
    save(DEFAULT_PREFERENCES)
  }, [])

  const value = useMemo<PreferencesValue>(
    () => ({ ...preferences, setPreference, reset }),
    [preferences, setPreference, reset],
  )

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>
}

export function usePreferences(): PreferencesValue {
  return useContext(PreferencesContext)
}
