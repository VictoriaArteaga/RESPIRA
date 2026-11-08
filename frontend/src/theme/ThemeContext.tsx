import { createContext, useContext, useLayoutEffect, useMemo, useState, type PropsWithChildren } from 'react'

export type Theme = 'light' | 'dark'

interface ThemeValue {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const STORAGE_KEY = 'respira.theme'

function storedTheme(): Theme {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

const ThemeContext = createContext<ThemeValue>({ theme: 'light', setTheme: () => undefined })

export function ThemeProvider({ children }: PropsWithChildren) {
  const [theme, setThemeState] = useState<Theme>(storedTheme)

  // La clase "dark" en <html> activa los tokens oscuros definidos en index.css.
  useLayoutEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const value = useMemo<ThemeValue>(
    () => ({
      theme,
      setTheme: (next) => {
        setThemeState(next)
        try {
          window.localStorage.setItem(STORAGE_KEY, next)
        } catch {
          // Sin almacenamiento disponible: la preferencia solo dura la sesión.
        }
      },
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeValue {
  return useContext(ThemeContext)
}
