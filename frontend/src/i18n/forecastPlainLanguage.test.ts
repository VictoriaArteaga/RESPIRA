import { describe, expect, it } from 'vitest'
import { en, es } from './translations'

// La pantalla de predicción la usa personal de salud, no personal de sistemas: sus textos no deben traer jerga
// estadística ni de programación (siglas de métricas, "modelo", "variables", nombres de scripts...).
const TECHNICAL: Record<'es' | 'en', RegExp> = {
  es: /\b(MAE|RMSE|AUC|percentil(es)?|P50|P75|P90|persistencia|rezagos?|entrenad[oa]s?|validaci[oó]n|variables?|modelos?|dataset|backend|scripts?|train_forecast|horizonte|intervalo|par[aá]metros?|algoritmo)\b/i,
  en: /\b(MAE|RMSE|AUC|percentiles?|P50|P75|P90|persistence|lags?|trained|training|validation|variables?|models?|dataset|backend|scripts?|train_forecast|horizon|intervals?|parameters?|algorithm)\b/i,
}

const dictionaries = { es: es as Record<string, string>, en: en as Record<string, string> }

describe('pantalla de predicción: textos en lenguaje claro', () => {
  for (const language of ['es', 'en'] as const) {
    it(`no usa jerga técnica (${language})`, () => {
      const offenders = Object.entries(dictionaries[language])
        .filter(([key]) => key.startsWith('fc.') || key === 'nav.forecast')
        // {mae}, {p75}... son marcadores que se reemplazan por números: la persona nunca los ve.
        .filter(([, text]) => TECHNICAL[language].test(text.replace(/\{[^}]*\}/g, '')))
        .map(([key, text]) => `${key}: ${text.slice(0, 80)}`)
      expect(offenders).toEqual([])
    })
  }

  it('los porcentajes de las explicaciones se dicen como "de cada 100"', () => {
    for (const key of ['fc.sigHistory', 'fc.chExceed75', 'fc.chExceed90']) {
      expect(es[key as keyof typeof es]).toMatch(/de cada 100/)
      expect(en[key as keyof typeof en]).toMatch(/out of every 100/)
      expect(es[key as keyof typeof es]).not.toMatch(/\}%/)
    }
  })
})
