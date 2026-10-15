import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchRiskMap } from '../services/riskService'
import type { MunicipalityRisk, RiskLevel, RiskMap } from '../types/risk'

const colors: Record<RiskLevel, string> = { low: '#27834a', moderate: '#d9a400', high: '#c83d3d', no_data: '#94a3b8' }
const labels: Record<RiskLevel, string> = { low: 'Bajo', moderate: 'Moderado', high: 'Alto', no_data: 'Sin datos' }

function FitMunicipalities({ items }: { items: MunicipalityRisk[] }) {
  const map = useMap()
  useEffect(() => {
    if (items.length) map.fitBounds(items.map((item) => [item.latitude, item.longitude]), { padding: [36, 36] })
  }, [items, map])
  return null
}

export function RiskMapPage() {
  const [data, setData] = useState<RiskMap | null>(null)
  const [selected, setSelected] = useState<MunicipalityRisk | null>(null)
  const [year, setYear] = useState<number | undefined>()
  const [week, setWeek] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(null)
    fetchRiskMap(year, week, controller.signal).then((result) => {
      setData(result)
      setSelected((current) => result.municipalities.find((item) => item.municipality_id === current?.municipality_id) ?? null)
    }).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'No fue posible obtener la información.')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [year, week])

  const changeYear = (value: string) => { setYear(value ? Number(value) : undefined); setWeek(undefined) }
  return <div className="space-y-6">
    <header><p className="text-sm font-medium text-sky-800">Vigilancia territorial</p><h1 className="mt-1 text-2xl font-bold tracking-tight">Mapa de riesgo por municipio</h1><p className="mt-2 text-sm text-respira-muted">Comparación descriptiva de casos con la misma semana de años anteriores. No es un diagnóstico ni una predicción.</p></header>
    <Card className="flex flex-wrap items-end gap-4 p-4">
      <label className="grid gap-1 text-sm font-medium">Año<select className="rounded-lg border border-respira-border bg-white px-3 py-2" value={year ?? ''} onChange={(event) => changeYear(event.target.value)}><option value="">Más reciente</option>{(data?.available_years ?? []).map((value) => <option key={value}>{value}</option>)}</select></label>
      <label className="grid gap-1 text-sm font-medium">Semana epidemiológica<select className="rounded-lg border border-respira-border bg-white px-3 py-2" value={week ?? ''} onChange={(event) => setWeek(event.target.value ? Number(event.target.value) : undefined)}><option value="">Última disponible</option>{Array.from({ length: 53 }, (_, index) => index + 1).map((value) => <option key={value} value={value}>Semana {value}</option>)}</select></label>
      <p className="ml-auto text-xs text-respira-muted">Datos sintéticos de desarrollo</p>
    </Card>
    {loading ? <Card><Loading /></Card> : error ? <Card><ErrorState message={error} /></Card> : !data?.municipalities.length ? <Card><EmptyState>No hay datos disponibles para los filtros seleccionados.</EmptyState></Card> : <div className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_minmax(280px,0.8fr)]">
      <Card className="overflow-hidden"><div className="flex flex-wrap gap-4 border-b border-respira-border px-5 py-4 text-sm">{(['low','moderate','high','no_data'] as RiskLevel[]).map((level) => <span key={level} className="inline-flex items-center gap-2"><i className="h-3 w-3 rounded-full" style={{ backgroundColor: colors[level] }} />{labels[level]}</span>)}</div><MapContainer center={[1.3, -78]} zoom={8} scrollWheelZoom className="h-[520px] w-full"><TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><FitMunicipalities items={data.municipalities}/>{data.municipalities.map((item) => <CircleMarker key={item.municipality_id} center={[item.latitude,item.longitude]} radius={selected?.municipality_id === item.municipality_id ? 12 : 9} pathOptions={{ color: '#fff', weight: 2, fillColor: colors[item.risk_level], fillOpacity: .92 }} eventHandlers={{ click: () => setSelected(item) }}><Tooltip>{item.municipality} · Riesgo {labels[item.risk_level].toLowerCase()}</Tooltip></CircleMarker>)}</MapContainer></Card>
      <Card className="p-5">{selected ? <><p className="text-xs font-semibold uppercase tracking-wide text-respira-muted">{selected.department} · Semana {selected.week ?? data.week}, {selected.year ?? data.year}</p><h2 className="mt-2 text-xl font-bold">{selected.municipality}</h2><div className="mt-5 grid grid-cols-2 gap-3"><Metric label="Casos observados" value={selected.current_cases?.toLocaleString('es-CO') ?? 'Sin datos'}/><Metric label="Promedio histórico" value={selected.historical_average?.toLocaleString('es-CO') ?? '—'}/><Metric label="Variación" value={selected.variation_percent === null ? '—' : `${selected.variation_percent > 0 ? '+' : ''}${selected.variation_percent}%`}/><Metric label="Nivel" value={labels[selected.risk_level]}/></div><p className="mt-5 text-xs leading-5 text-respira-muted">Clasificación estadística de apoyo al monitoreo. Bajo: variación menor a 20%; moderado: 20% a menos de 50%; alto: 50% o más respecto a la media histórica de la misma semana.</p></> : <EmptyState>Selecciona un municipio en el mapa para consultar sus datos.</EmptyState>}</Card>
    </div>}
  </div>
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-[#F8FAFC] p-3"><p className="text-xs text-respira-muted">{label}</p><p className="mt-1 font-semibold tabular-nums">{value}</p></div> }
