import { useEffect, useMemo, useState } from 'react'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchCases } from '../services/caseService'
import { fetchMunicipalities } from '../services/municipalityService'
import type { Municipality } from '../types/municipality'
import type { IraCase } from '../types/case'

export function CasesPage() {
  const [cases, setCases] = useState<IraCase[]>([])
  const [municipalities, setMunicipalities] = useState<Municipality[]>([])
  const [year, setYear] = useState('')
  const [week, setWeek] = useState('')
  const [municipalityId, setMunicipalityId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([fetchCases({}, controller.signal), fetchMunicipalities(controller.signal)])
      .then(([caseData, municipalityData]) => { setCases(caseData); setMunicipalities(municipalityData) })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : 'No fue posible obtener la información del servidor.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [])

  const years = useMemo(() => [...new Set(cases.map((record) => record.year))].sort((a, b) => b - a), [cases])
  const weeks = useMemo(() => [...new Set(cases.filter((record) => !year || record.year === Number(year)).map((record) => record.epidemiological_week))].sort((a, b) => a - b), [cases, year])
  const filteredCases = useMemo(() => cases.filter((record) =>
    (!year || record.year === Number(year)) &&
    (!week || record.epidemiological_week === Number(week)) &&
    (!municipalityId || record.municipality_id === Number(municipalityId)),
  ), [cases, municipalityId, week, year])

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-sky-800">Registros epidemiológicos</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Casos IRA</h1>
        <p className="mt-2 text-sm text-respira-muted">Consulta de casos por municipio y semana epidemiológica.</p>
      </div>
      <Card className="flex flex-wrap items-end gap-4 p-4">
        <label className="grid gap-1 text-sm font-medium">Año<select className="rounded-lg border border-respira-border bg-white px-3 py-2" value={year} onChange={(event) => { setYear(event.target.value); setWeek('') }}><option value="">Todos</option>{years.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label className="grid gap-1 text-sm font-medium">Semana<select className="rounded-lg border border-respira-border bg-white px-3 py-2" value={week} onChange={(event) => setWeek(event.target.value)}><option value="">Todas</option>{weeks.map((value) => <option key={value} value={value}>Semana {value}</option>)}</select></label>
        <label className="grid gap-1 text-sm font-medium">Municipio<select className="min-w-48 rounded-lg border border-respira-border bg-white px-3 py-2" value={municipalityId} onChange={(event) => setMunicipalityId(event.target.value)}><option value="">Todos</option>{municipalities.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <p className="ml-auto text-xs text-respira-muted">Datos sintéticos de desarrollo</p>
      </Card>
      {loading ? (
        <Card><Loading /></Card>
      ) : error ? (
        <Card><ErrorState message={error} /></Card>
      ) : cases.length === 0 ? (
        <Card><EmptyState /></Card>
      ) : filteredCases.length === 0 ? (
        <Card><EmptyState>No hay registros para los filtros seleccionados.</EmptyState></Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-[#F2F5F5] text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">Año</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Semana epidemiológica</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Municipio (ID)</th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">Casos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-respira-border">
                {filteredCases.map((record) => (
                  <tr key={record.id} className="hover:bg-sky-50/70">
                    <td className="px-6 py-3.5">{record.year}</td>
                    <td className="px-6 py-3.5">Semana {record.epidemiological_week}</td>
                    <td className="px-6 py-3.5 text-respira-muted">{municipalities.find((item) => item.id === record.municipality_id)?.name ?? record.municipality_id}</td>
                    <td className="px-6 py-3.5 text-right font-semibold tabular-nums">{record.cases.toLocaleString('es-CO')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
