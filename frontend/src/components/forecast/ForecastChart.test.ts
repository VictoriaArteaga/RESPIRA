import { describe, expect, it } from 'vitest'
import type { ForecastPrediction, ForecastResult } from '../../types/forecast'
import { buildRows } from './ForecastChart'

function prediction(horizon: number, value: number): ForecastPrediction {
  return {
    horizon_weeks: horizon, target_year: 2023, target_week: horizon, target_week_start: '2023-01-01', target_week_end: '2023-01-07',
    predicted_cases: value, interval_low: value - 10, interval_high: value + 10, reference_cases: 200, change_vs_reference_pct: 0,
    trend: 'estable', observed_cases: null, absolute_error: null,
  }
}

// 100 semanas de historial (2021-2022) y estimaciones a 2 y 3 semanas.
const data = {
  history: Array.from({ length: 100 }, (_, index) => ({
    year: 2021 + Math.floor(index / 52), week: (index % 52) + 1, week_end: '2022-01-01', cases: 100 + index, status: 'OBSERVADO',
  })),
  predictions: [prediction(2, 210), prediction(3, 220)],
} as unknown as ForecastResult

describe('gráfica de predicción: la estimación se amplía para que se lea', () => {
  it('con 26 semanas, la zona de estimación ocupa cerca de un cuarto del ancho y va ordenada después de la última semana', () => {
    const { rows, stretch } = buildRows(data, 26)
    const observed = rows.filter((row) => !row.isPrediction)
    const future = rows.filter((row) => row.isPrediction)
    expect(observed).toHaveLength(26)
    expect(future.map((row) => row.predicted)).toEqual([210, 220])
    const origin = observed[observed.length - 1].x
    expect(future[0].x).toBeGreaterThan(origin)
    expect(future[1].x).toBeGreaterThan(future[0].x)
    expect(stretch).toBeGreaterThan(2) // 0,3 × 26 / 3 ≈ 2,6 semanas por semana real
    expect(stretch).toBeLessThanOrEqual(3)
    const share = (future[1].x - origin) / future[1].x
    expect(share).toBeGreaterThan(0.2)
    expect(share).toBeLessThan(0.35)
  })

  it('la estimación parte del último valor observado y no se inventan semanas intermedias', () => {
    const { rows } = buildRows(data, 26)
    const last = rows.filter((row) => !row.isPrediction).at(-1)!
    expect(last.predicted).toBe(last.cases)
    expect(last.band).toEqual([last.cases, last.cases])
    expect(rows).toHaveLength(26 + 2)
  })

  it('con todo el historial la ampliación tiene tope: no deforma el tiempo sin límite', () => {
    const { rows, stretch } = buildRows(data, Infinity)
    expect(rows.filter((row) => !row.isPrediction)).toHaveLength(100)
    expect(stretch).toBe(3)
  })

  it('con pocas semanas visibles no amplía de más: nunca por debajo de la escala real', () => {
    const { stretch } = buildRows(data, 3)
    expect(stretch).toBeGreaterThanOrEqual(1)
  })
})
