import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import { en, es, type TranslationKey } from './translations'

export type Language = 'es' | 'en'

type Params = Record<string, string | number>

interface I18nValue {
  language: Language
  /** Configuración regional para formatear números y fechas. */
  locale: string
  setLanguage: (language: Language) => void
  t: (key: TranslationKey, params?: Params) => string
}

const STORAGE_KEY = 'respira.language'
const LOCALES: Record<Language, string> = { es: 'es-CO', en: 'en-US' }
const dictionaries: Record<Language, Record<TranslationKey, string>> = { es, en }

function translate(language: Language, key: TranslationKey, params?: Params): string {
  const template = dictionaries[language][key] ?? es[key]
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

function storedLanguage(): Language {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value === 'en' ? 'en' : 'es'
  } catch {
    return 'es'
  }
}

// Valor por defecto (español) para que los componentes funcionen también fuera del proveedor, p. ej. en pruebas.
const I18nContext = createContext<I18nValue>({
  language: 'es',
  locale: LOCALES.es,
  setLanguage: () => undefined,
  t: (key, params) => translate('es', key, params),
})

export function I18nProvider({ children }: PropsWithChildren) {
  const [language, setLanguageState] = useState<Language>(storedLanguage)

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  const value = useMemo<I18nValue>(
    () => ({
      language,
      locale: LOCALES[language],
      setLanguage: (next) => {
        setLanguageState(next)
        try {
          window.localStorage.setItem(STORAGE_KEY, next)
        } catch {
          // Sin almacenamiento disponible: la preferencia solo dura la sesión.
        }
      },
      t: (key, params) => translate(language, key, params),
    }),
    [language],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nValue {
  return useContext(I18nContext)
}
