import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { CaseTrendChart } from '../components/dashboard/CaseTrendChart'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchCases } from '../services/caseService'
import { fetchMunicipality } from '../services/municipalityService'
import { fetchMunicipalityRisk, fetchEndemicChannel } from '../services/riskService'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'
import type { EndemicChannel, MunicipalityRisk } from '../types/risk'

const riskLabels = { low: 'Bajo', moderate: 'Moderado', high: 'Alto', no_data: 'Sin datos' }

export function MunicipalityDetailPage() {
  const { id } = useParams()
  const municipalityId = Number(id)
  const [municipality, setMunicipality] = useState<Municipality | null>(null)
  const [cases, setCases] = useState<IraCase[]>([])
  const [risk, setRisk] = useState<MunicipalityRisk | null>(null)
  const [channel, setChannel] = useState<EndemicChannel | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    if (!Number.isInteger(municipalityId) || municipalityId < 1) {
      setError('El identificador del municipio no es válido.')
      setLoading(false)
      return () => controller.abort()
    }
    setLoading(true)
    setError(null)
    Promise.all([fetchMunicipality(municipalityId, controller.signal), fetchCases({ municipality_id: municipalityId }, controller.signal)])
      .then(async ([municipalityData, caseData]) => {
        setMunicipality(municipalityData)
        setCases(caseData)
        const latest = [...caseData].sort((a, b) => b.year - a.year || b.epidemiological_week - a.epidemiological_week)[0]
        if (latest) {
          const [riskData, channelData] = await Promise.all([
            fetchMunicipalityRisk(municipalityId, latest.year, latest.epidemiological_week, controller.signal),
            fetchEndemicChannel(municipalityId, latest.year, controller.signal),
          ])
          setRisk(riskData)
          setChannel(channelData)
        }
      })
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'No fue posible obtener la información del municipio.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [municipalityId])

  const latest = [...cases].sort((a, b) => b.year - a.year || b.epidemiological_week - a.epidemiological_week)[0]
  const total = cases.reduce((sum, item) => sum + item.cases, 0)
  return <div className="space-y-6">
    <Link to="/municipalities" className="inline-flex items-center gap-2 text-sm font-semibold text-sky-800 hover:underline"><ArrowLeft size={16}/>Volver a municipios</Link>
    {loading ? <Card><Loading/></Card> : error ? <Card><ErrorState message={error}/></Card> : !municipality ? <Card><EmptyState/></Card> : <>
      <header><p className="text-sm font-medium text-sky-800">{municipality.department} · Perfil territorial</p><h1 className="mt-1 text-2xl font-bold tracking-tight">{municipality.name}</h1><p className="mt-2 text-sm text-respira-muted">Consulta descriptiva de registros sintéticos de desarrollo. No son datos oficiales de SIVIGILA.</p></header>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[
        ['Casos registrados', total.toLocaleString('es-CO')],
        ['Último periodo', latest ? `${latest.year} · Semana ${latest.epidemiological_week}` : 'Sin registros'],
        ['Riesgo estadístico', risk ? riskLabels[risk.risk_level] : 'Sin datos'],
        ['Semanas del canal', channel?.weeks.length ?? 0],
      ].map(([label, value]) => <Card key={label} className="p-4"><p className="text-xs text-respira-muted">{label}</p><p className="mt-2 text-xl font-bold">{value}</p></Card>)}</div>
      {!cases.length ? <Card><EmptyState>Este municipio no tiene registros de casos en el conjunto de desarrollo.</EmptyState></Card> : <>
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]"><CaseTrendChart cases={cases}/><Card className="p-5"><h2 className="font-semibold">Riesgo del último periodo</h2><p className="mt-1 text-sm text-respira-muted">{risk?.year} · Semana {risk?.week}</p><dl className="mt-4 space-y-3 text-sm"><div className="flex justify-between gap-3"><dt>Casos observados</dt><dd className="font-semibold">{risk?.current_cases ?? 'Sin datos'}</dd></div><div className="flex justify-between gap-3"><dt>Promedio histórico</dt><dd className="font-semibold">{risk?.historical_average ?? 'Sin referencia'}</dd></div><div className="flex justify-between gap-3"><dt>Variación</dt><dd className="font-semibold">{risk?.variation_percent == null ? '—' : `${risk.variation_percent > 0 ? '+' : ''}${risk.variation_percent}%`}</dd></div></dl><p className="mt-4 text-xs leading-5 text-respira-muted">Clasificación descriptiva frente al promedio de la misma semana en años previos; no constituye diagnóstico ni predicción.</p><Link to="/alerts" className="mt-4 inline-block text-sm font-semibold text-sky-800 hover:underline">Consultar alertas</Link></Card></div>
        {latest && <Card className="p-5"><h2 className="font-semibold">Variables del último registro</h2><p className="mt-1 text-xs text-respira-muted">Variables sintéticas disponibles en el conjunto de desarrollo · {latest.year}, semana {latest.epidemiological_week}</p><dl className="mt-4 grid gap-4 sm:grid-cols-3">{[['Temperatura', `${latest.temperature} °C`], ['Precipitación', `${latest.precipitation} mm`], ['Humedad', `${latest.humidity}%`]].map(([label, value]) => <div key={label}><dt className="text-xs text-respira-muted">{label}</dt><dd className="mt-1 font-semibold">{value}</dd></div>)}</dl></Card>}
        <Card className="p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Canal endémico</h2><p className="mt-1 text-xs text-respira-muted">{channel?.weeks.length ?? 0} semanas con observaciones para {channel?.year ?? 'el periodo disponible'}.</p></div><Link to="/endemic" className="text-sm font-semibold text-sky-800 hover:underline">Abrir análisis del canal</Link></div><p className="mt-3 text-sm text-respira-muted">El análisis compara las observaciones con percentiles históricos por semana. La vista completa permite seleccionar municipio y año.</p></Card>
      </>}
    </>}
  </div>
}
