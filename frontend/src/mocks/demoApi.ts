// Datos de demostración para visualizar la interfaz sin depender del servidor.
// Se activan con VITE_DEMO_DATA=true (ver .env.example). Conviven dos conjuntos: 10 municipios SIMULADOS (2021-2025,
// sintéticos, marcados "(simulado)") y los 64 municipios REALES de Nariño con las atenciones por IRA de SIVIGILA 2012-2022.
import realData from './real-data.json'
import type { DashboardSummary } from '../types/dashboard'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'
import type {
  AlertResponse,
  EndemicChannel,
  EndemicPoint,
  EpidemiologicalAlert,
  MunicipalityRisk,
  RiskLevel,
  RiskMap,
} from '../types/risk'

const YEARS = [2021, 2022, 2023, 2024, 2025]
const WEEKS_PER_YEAR = 52

// Municipio, latitud, longitud y nivel base de casos semanales.
const MUNICIPALITY_SEED: Array<[string, number, number, number]> = [
  ['Pasto', 1.2136, -77.2811, 34],
  ['Ipiales', 0.83, -77.6444, 22],
  ['Tumaco', 1.8067, -78.7647, 28],
  ['Túquerres', 1.0865, -77.6186, 14],
  ['La Unión', 1.6045, -77.131, 9],
  ['Samaniego', 1.3365, -77.595, 8],
  ['Barbacoas', 1.6717, -78.1398, 11],
  ['Sandoná', 1.2867, -77.468, 7],
  ['Cumbal', 0.908, -77.791, 10],
  ['Guaitarilla', 1.131, -77.548, 6],
]

// Brotes simulados en las últimas semanas para que alertas y mapa muestren los tres niveles de riesgo.
const OUTBREAKS: Record<string, number> = {
  Pasto: 1.85,
  Tumaco: 1.65,
  Ipiales: 1.32,
  Cumbal: 1.28,
}

function mulberry32(seed: number): () => number {
  let state = seed
  return () => {
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const simulatedMunicipalities: Municipality[] = MUNICIPALITY_SEED.map(([name, latitude, longitude], index) => ({
  id: index + 1,
  name,
  department: 'Nariño',
  latitude,
  longitude,
}))

const simulatedCases: IraCase[] = (() => {
  const random = mulberry32(20250518)
  const records: IraCase[] = []
  let id = 1
  for (const municipality of simulatedMunicipalities) {
    const base = MUNICIPALITY_SEED[municipality.id - 1][3]
    for (const year of YEARS) {
      for (let week = 1; week <= WEEKS_PER_YEAR; week += 1) {
        // Dos picos estacionales (temporadas de lluvias) y una leve tendencia al alza por año.
        const seasonal = 1 + 0.35 * Math.sin(((week - 8) / WEEKS_PER_YEAR) * 4 * Math.PI)
        const trend = 1 + (year - YEARS[0]) * 0.03
        const noise = 0.85 + random() * 0.3
        let value = base * seasonal * trend * noise
        if (year === YEARS[YEARS.length - 1] && week > WEEKS_PER_YEAR - 3) {
          value *= OUTBREAKS[municipality.name] ?? 1
        }
        records.push({
          id: id++,
          municipality_id: municipality.id,
          epidemiological_week: week,
          year,
          cases: Math.max(0, Math.round(value)),
          temperature: Number((12 + 6 * random() + (municipality.name === 'Tumaco' ? 12 : 0)).toFixed(1)),
          precipitation: Number((60 + 140 * random() * (1 + 0.3 * Math.sin((week / 52) * 4 * Math.PI))).toFixed(1)),
          humidity: Number((68 + 22 * random()).toFixed(1)),
        })
      }
    }
  }
  return records
})()

// ---- Datos reales: atenciones por IRA notificadas en <5 años (SIVIGILA 995), 64 municipios, 2012-2022 ----
// Se generan con data/scripts/respira_v2/10_exportar_demo_frontend.py. Las semanas sin reporte vienen como null y no se
// dibujan: nunca se convierten en cero. No traen clima en la interfaz (la IA lo usa por su lado).
interface RealData {
  semanas: Array<[number, number]>
  municipios: Array<{ c: string; n: string; lat: number; lon: number; v: Array<number | null> }>
}
const real = realData as unknown as RealData
const REAL_YEARS = [...new Set(real.semanas.map(([year]) => year))]

// El id de un municipio real es su código DIVIPOLA (5 dígitos), así nunca choca con los ids 1-10 de los simulados.
const realMunicipalities: Municipality[] = real.municipios.map((m) => ({
  id: Number(m.c),
  name: m.n,
  department: 'Nariño',
  latitude: m.lat,
  longitude: m.lon,
}))

const realCases: IraCase[] = (() => {
  const records: IraCase[] = []
  let id = 100000
  for (const m of real.municipios) {
    m.v.forEach((value, index) => {
      if (value === null) return
      const [year, week] = real.semanas[index]
      records.push({
        id: id++,
        municipality_id: Number(m.c),
        epidemiological_week: week,
        year,
        cases: value,
        temperature: null,
        precipitation: null,
        humidity: null,
      })
    })
  }
  return records
})()

// Los municipios simulados llevan "(simulado)" para distinguirlos de los reales con el mismo nombre (p. ej. Pasto).
const municipalities: Municipality[] = [
  ...realMunicipalities,
  ...simulatedMunicipalities.map((m) => ({ ...m, name: `${m.name} (simulado)`, simulated: true })),
]
// Nariño tiene 64 municipios. Los simulados son copias de municipios que ya están entre esos 64 (con datos de prueba),
// por eso no cuentan como municipios adicionales en los totales.
const NARINO_MUNICIPALITIES = municipalities.filter((item) => !item.simulated).length
const cases: IraCase[] = [...realCases, ...simulatedCases]
const AVAILABLE_YEARS = [...new Set([...REAL_YEARS, ...YEARS])].sort((a, b) => b - a)

const casesByMunicipality = new Map<number, IraCase[]>()
for (const record of cases) {
  const list = casesByMunicipality.get(record.municipality_id)
  if (list) list.push(record)
  else casesByMunicipality.set(record.municipality_id, [record])
}

const latestYear = YEARS[YEARS.length - 1]
const latestWeek = WEEKS_PER_YEAR

function percentile(sorted: number[], fraction: number): number {
  if (sorted.length === 0) return 0
  const position = (sorted.length - 1) * fraction
  const lower = Math.floor(position)
  const upper = Math.ceil(position)
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower)
}

const round1 = (value: number) => Math.round(value * 10) / 10

function classify(variation: number): RiskLevel {
  if (variation >= 50) return 'high'
  if (variation >= 20) return 'moderate'
  return 'low'
}

function casesOf(municipalityId: number): IraCase[] {
  return casesByMunicipality.get(municipalityId) ?? []
}

function riskFor(municipality: Municipality, year: number, week: number): MunicipalityRisk {
  const own = casesOf(municipality.id)
  const current = own.find((record) => record.year === year && record.epidemiological_week === week)
  const previous = own.filter((record) => record.year < year && record.epidemiological_week === week)
  const base = {
    municipality_id: municipality.id,
    municipality: municipality.name,
    department: municipality.department,
    latitude: municipality.latitude,
    longitude: municipality.longitude,
    year,
    week,
  }
  if (!current || previous.length === 0) {
    return {
      ...base,
      current_cases: current?.cases ?? null,
      historical_average: null,
      variation_percent: null,
      risk_level: 'no_data',
    }
  }
  const average = previous.reduce((sum, record) => sum + record.cases, 0) / previous.length
  const variation = average === 0 ? 0 : ((current.cases - average) / average) * 100
  return {
    ...base,
    current_cases: current.cases,
    historical_average: round1(average),
    variation_percent: round1(variation),
    risk_level: classify(variation),
  }
}

function period(params: URLSearchParams): { year: number; week: number } {
  const year = Number(params.get('year')) || latestYear
  const week = Number(params.get('week')) || (year === latestYear ? latestWeek : WEEKS_PER_YEAR)
  return { year, week }
}

function riskMap(params: URLSearchParams): RiskMap {
  const { year, week } = period(params)
  return {
    year,
    week,
    available_years: AVAILABLE_YEARS,
    municipalities: municipalities.map((municipality) => riskFor(municipality, year, week)),
  }
}

function alerts(params: URLSearchParams): AlertResponse {
  const { year, week } = period(params)
  const list: EpidemiologicalAlert[] = municipalities
    .map((municipality) => riskFor(municipality, year, week))
    .filter((risk) => risk.risk_level === 'moderate' || risk.risk_level === 'high')
    .map((risk) => ({
      municipality_id: risk.municipality_id,
      municipality: risk.municipality,
      year,
      week,
      observed_cases: risk.current_cases ?? 0,
      historical_average: risk.historical_average ?? 0,
      variation_percent: risk.variation_percent ?? 0,
      risk_level: risk.risk_level as 'moderate' | 'high',
      reason: `Los casos de la semana ${week} superan en ${risk.variation_percent}% el promedio histórico de la misma semana en años anteriores.`,
    }))
    .sort((left, right) => right.variation_percent - left.variation_percent)
  return { year, week, available_years: AVAILABLE_YEARS, alerts: list }
}

function endemicChannel(municipality: Municipality, params: URLSearchParams): EndemicChannel {
  const year = Number(params.get('year')) || latestYear
  const own = casesOf(municipality.id)
  const observed = own
    .filter((record) => record.year === year)
    .sort((a, b) => a.epidemiological_week - b.epidemiological_week)
  const weeks: EndemicPoint[] = observed.map((record) => {
    const history = own
      .filter((item) => item.year < year && item.epidemiological_week === record.epidemiological_week)
      .map((item) => item.cases)
      .sort((a, b) => a - b)
    const hasHistory = history.length > 0
    return {
      week: record.epidemiological_week,
      observed_cases: record.cases,
      historical_median: hasHistory ? round1(percentile(history, 0.5)) : null,
      lower_limit: hasHistory ? round1(percentile(history, 0.25)) : null,
      upper_limit: hasHistory ? round1(percentile(history, 0.75)) : null,
      upper_alert_limit: hasHistory ? round1(percentile(history, 0.9)) : null,
    }
  })
  const values = observed.map((record) => record.cases).sort((a, b) => a - b)
  const total = values.reduce((sum, value) => sum + value, 0)
  const lastWeek = observed[observed.length - 1]?.epidemiological_week ?? null
  return {
    municipality_id: municipality.id,
    municipality: municipality.name,
    year,
    available_years: AVAILABLE_YEARS,
    statistics: values.length
      ? {
          total_cases: total,
          average: round1(total / values.length),
          median: round1(percentile(values, 0.5)),
          minimum: values[0],
          maximum: values[values.length - 1],
          risk_level: lastWeek ? riskFor(municipality, year, lastWeek).risk_level : 'no_data',
          latest_week: lastWeek,
        }
      : null,
    weeks,
  }
}

/** Indicadores del resumen: solo con los datos REALES (SIVIGILA, 64 municipios). Los simulados no suman a estas cifras. */
function dashboard(): DashboardSummary {
  const totals = new Map<number, number>()
  for (const record of realCases)
    totals.set(record.municipality_id, (totals.get(record.municipality_id) ?? 0) + record.cases)
  const [topId] = [...totals.entries()].sort((a, b) => b[1] - a[1])[0]
  const totalCases = realCases.reduce((sum, record) => sum + record.cases, 0)
  const lastRealWeek = real.semanas[real.semanas.length - 1][1]
  return {
    total_municipalities: NARINO_MUNICIPALITIES,
    total_cases: totalCases,
    average_cases: round1(totalCases / NARINO_MUNICIPALITIES),
    municipality_with_most_cases: realMunicipalities.find((item) => item.id === topId)?.name ?? null,
    last_epidemiological_week: lastRealWeek,
    total_records: realCases.length,
  }
}

/** Resuelve una ruta de la API con datos de demostración; devuelve undefined si la ruta no se simula. */
export function resolveDemo(path: string): unknown {
  const [pathname, search = ''] = path.split('?')
  const params = new URLSearchParams(search)

  if (pathname === '/api/dashboard') return dashboard()
  if (pathname === '/api/municipalities') return municipalities
  if (pathname === '/api/cases') {
    const municipalityId = params.get('municipality_id')
    const year = params.get('year')
    const week = params.get('epidemiological_week')
    return cases.filter(
      (record) =>
        (!municipalityId || record.municipality_id === Number(municipalityId)) &&
        (!year || record.year === Number(year)) &&
        (!week || record.epidemiological_week === Number(week)),
    )
  }
  if (pathname === '/api/risk-map') return riskMap(params)
  if (pathname === '/api/alerts') return alerts(params)

  const match = pathname.match(/^\/api\/municipalities\/(\d+)(?:\/(risk|endemic-channel))?$/)
  if (match) {
    const municipality = municipalities.find((item) => item.id === Number(match[1]))
    if (!municipality) return undefined
    if (match[2] === 'risk') {
      const { year, week } = period(params)
      return riskFor(municipality, year, week)
    }
    if (match[2] === 'endemic-channel') return endemicChannel(municipality, params)
    return municipality
  }
  return undefined
}
