import { useEffect, useState } from 'react'
import { AlertTriangle, Bell } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '../components/common/Badge'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchAlerts } from '../services/riskService'
import type { AlertResponse, EpidemiologicalAlert } from '../types/risk'

function AlertRow({ alert }: { alert: EpidemiologicalAlert }) {
  const high = alert.risk_level === 'high'
  return <article className="grid gap-3 border-t border-respira-border px-5 py-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
    <div>
      <div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold text-respira-text">{alert.municipality}</h2><Badge className={high ? 'bg-rose-100 text-rose-900' : 'bg-amber-100 text-amber-950'}>{high ? 'Riesgo alto' : 'Vigilancia'}</Badge><span className="text-xs text-respira-muted">Semana {alert.week}, {alert.year}</span></div>
      <p className="mt-2 text-sm leading-6 text-respira-muted">{alert.reason}</p>
      <p className="mt-1 text-xs text-respira-muted">Regla estadística determinista; no se utiliza inteligencia artificial.</p>
    </div>
    <div className="flex items-center justify-between gap-5 md:justify-end">
      <div className="text-right text-sm"><p><strong>{alert.observed_cases.toLocaleString('es-CO')}</strong> observados</p><p className="text-xs text-respira-muted">Promedio histórico: {alert.historical_average.toLocaleString('es-CO')} · {alert.variation_percent > 0 ? '+' : ''}{alert.variation_percent}%</p></div>
      <Link className="text-sm font-semibold text-sky-800 underline-offset-4 hover:underline" to={`/municipalities/${alert.municipality_id}`}>Ver municipio</Link>
    </div>
  </article>
}

export function AlertsPage() {
  const [data, setData] = useState<AlertResponse | null>(null)
  const [level, setLevel] = useState<'all' | 'moderate' | 'high'>('all')
  const [year, setYear] = useState<number | undefined>()
  const [week, setWeek] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchAlerts(year, week, controller.signal)
      .then(setData)
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'No fue posible obtener las alertas.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [year, week])

  const alerts = (data?.alerts ?? []).filter((item) => level === 'all' || item.risk_level === level)
  return <div className="space-y-6">
    <header><p className="text-sm font-medium text-sky-800">Seguimiento epidemiológico</p><h1 className="mt-1 text-2xl font-bold tracking-tight">Alertas</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-respira-muted">Desviaciones calculadas con reglas reproducibles sobre los casos registrados y el promedio histórico de la misma semana.</p></header>
    <Card className="flex flex-wrap items-end gap-3 p-4"><span className="mr-auto flex items-center gap-2 pb-2 text-sm font-semibold"><Bell size={17} aria-hidden="true"/> Periodo {data?.year ? `${data.year} · Semana ${data.week}` : 'más reciente disponible'}</span><label className="grid gap-1 text-xs font-medium">Año<select className="rounded-lg border border-respira-border bg-white px-3 py-2 text-sm" value={year ?? ''} onChange={(event) => { setYear(event.target.value ? Number(event.target.value) : undefined); setWeek(undefined) }}><option value="">Más reciente</option>{(data?.available_years ?? []).map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label className="grid gap-1 text-xs font-medium">Semana<select className="rounded-lg border border-respira-border bg-white px-3 py-2 text-sm" value={week ?? ''} onChange={(event) => setWeek(event.target.value ? Number(event.target.value) : undefined)}><option value="">Última disponible</option>{Array.from({ length: 53 }, (_, index) => index + 1).map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label className="grid gap-1 text-xs font-medium">Nivel<select className="rounded-lg border border-respira-border bg-white px-3 py-2 text-sm" value={level} onChange={(event) => setLevel(event.target.value as typeof level)}><option value="all">Todos</option><option value="moderate">Vigilancia</option><option value="high">Riesgo alto</option></select></label><span className="w-full text-xs text-respira-muted">Datos sintéticos de desarrollo; no son registros oficiales de SIVIGILA.</span></Card>
    {loading ? <Card><Loading/></Card> : error ? <Card><ErrorState message={error}/></Card> : <Card className="overflow-hidden">{alerts.length ? <>{alerts.map((alert) => <AlertRow key={`${alert.municipality_id}-${alert.year}-${alert.week}`} alert={alert}/>)}</> : <EmptyState><span className="inline-flex items-center gap-2"><AlertTriangle size={16} aria-hidden="true"/> No hay alertas para este filtro y periodo.</span></EmptyState>}</Card>}
  </div>
}
