import { describe, expect, it } from 'vitest'
import type { IraCase } from '../types/case'
import type { DashboardSummary } from '../types/dashboard'
import type { Municipality } from '../types/municipality'
import type { EndemicChannel, RiskMap } from '../types/risk'
import { resolveDemo } from './demoApi'

const municipalities = resolveDemo('/api/municipalities') as Municipality[]
// Los municipios reales usan su código DIVIPOLA (5 dígitos) como id; los simulados, del 1 al 10.
const real = municipalities.filter((item) => item.id >= 10000)
const simulated = municipalities.filter((item) => item.id < 10000)
const casesOf = (id: number) => resolveDemo(`/api/cases?municipality_id=${id}`) as IraCase[]

describe('datos de demostración: los reales (2012-2022) y los simulados conviven', () => {
  it('incluye los 64 municipios reales y los 10 simulados, estos últimos marcados como tales', () => {
    expect(real).toHaveLength(64)
    expect(simulated).toHaveLength(10)
    expect(simulated.every((item) => item.name.endsWith('(simulado)'))).toBe(true)
    expect(real.some((item) => item.name.includes('simulado'))).toBe(false)
    // Pasto existe dos veces, pero se distingue por el nombre.
    expect(municipalities.filter((item) => item.name.startsWith('Pasto')).map((item) => item.name).sort()).toEqual([
      'Pasto',
      'Pasto (simulado)',
    ])
    expect(new Set(municipalities.map((item) => item.id)).size).toBe(74)
  })

  it('los años disponibles van de 2012 a 2025', () => {
    const map = resolveDemo('/api/risk-map?year=2018&week=10') as RiskMap
    expect(map.available_years[0]).toBe(2025)
    expect(map.available_years).toContain(2012)
    expect(map.available_years).toContain(2022)
    expect(map.municipalities).toHaveLength(74)
  })

  it('los datos reales de Pasto cubren 2012-2022 y nunca convierten una semana sin reporte en cero', () => {
    const pasto = real.find((item) => item.name === 'Pasto')!
    const records = casesOf(pasto.id)
    const years = records.map((item) => item.year)
    expect(Math.min(...years)).toBe(2012)
    expect(Math.max(...years)).toBe(2022)
    expect(records.length).toBeLessThanOrEqual(574)
    expect(records.every((item) => Number.isInteger(item.cases) && item.cases >= 0)).toBe(true)
    // Las 574 semanas del periodo no siempre tienen reporte: las que no lo tienen simplemente no aparecen.
    const sinReporte = real.reduce((total, item) => total + (574 - casesOf(item.id).length), 0)
    expect(sinReporte).toBe(2340)
  })

  it('los registros reales no traen clima inventado', () => {
    const pasto = real.find((item) => item.name === 'Pasto')!
    expect(casesOf(pasto.id).every((item) => item.temperature === null && item.precipitation === null)).toBe(true)
    const simulado = simulated[0]
    expect(casesOf(simulado.id).every((item) => typeof item.temperature === 'number')).toBe(true)
  })

  it('los simulados siguen siendo de 2021 a 2025', () => {
    const years = casesOf(simulated[0].id).map((item) => item.year)
    expect(Math.min(...years)).toBe(2021)
    expect(Math.max(...years)).toBe(2025)
  })

  it('el mapa de 2018 clasifica municipios reales con su propia historia', () => {
    const map = resolveDemo('/api/risk-map?year=2018&week=30') as RiskMap
    const pasto = map.municipalities.find((item) => item.municipality === 'Pasto')!
    expect(pasto.current_cases).not.toBeNull()
    expect(pasto.risk_level).not.toBe('no_data')
    // En 2018 los simulados aún no tienen datos.
    expect(map.municipalities.find((item) => item.municipality === 'Pasto (simulado)')!.risk_level).toBe('no_data')
  })

  it('el canal endémico de un municipio real se calcula con sus años anteriores', () => {
    const pasto = real.find((item) => item.name === 'Pasto')!
    const channel = resolveDemo(`/api/municipalities/${pasto.id}/endemic-channel?year=2022`) as EndemicChannel
    expect(channel.weeks.length).toBeGreaterThan(40)
    expect(channel.weeks.find((point) => point.week === 10)?.historical_median).not.toBeNull()
    expect(channel.available_years).toContain(2012)
  })

  it('los simulados son copias de municipios reales: no son municipios adicionales', () => {
    expect(simulated.every((item) => item.simulated === true)).toBe(true)
    expect(real.every((item) => !item.simulated)).toBe(true)
    for (const item of simulated) {
      const base = item.name.replace(' (simulado)', '')
      // "Tumaco" es "San Andrés de Tumaco" en la lista oficial de municipios.
      expect(real.some((candidate) => candidate.name.includes(base))).toBe(true)
    }
  })

  it('el resumen general cuenta los 64 municipios de Nariño una sola vez y el promedio es coherente', () => {
    const summary = resolveDemo('/api/dashboard') as DashboardSummary
    expect(summary.total_municipalities).toBe(64)
    expect(summary.total_records).toBeGreaterThan(34396 + 2600 - 1)
    expect(summary.average_cases).toBeCloseTo(summary.total_cases / 64, 1)
  })
})
