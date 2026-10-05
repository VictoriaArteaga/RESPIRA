import { useEffect, useMemo, useState } from 'react'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchCases } from '../services/caseService'
import { fetchMunicipalities } from '../services/municipalityService'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'

export function MunicipalitiesPage() {
  const [municipalities, setMunicipalities] = useState<Municipality[]>([])
  const [cases, setCases] = useState<IraCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([fetchMunicipalities(controller.signal), fetchCases({}, controller.signal)])
      .then(([municipalityData, caseData]) => {
        setMunicipalities(municipalityData)
        setCases(caseData)
      })
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

  const totals = useMemo(() => {
    const byMunicipality = new Map<number, { cases: number; year: number; week: number }>()
    for (const record of cases) {
      const current = byMunicipality.get(record.municipality_id) ?? {
        cases: 0,
        year: 0,
        week: 0,
      }
      current.cases += record.cases
      if (record.year > current.year || (record.year === current.year && record.epidemiological_week > current.week)) {
        current.year = record.year
        current.week = record.epidemiological_week
      }
      byMunicipality.set(record.municipality_id, current)
    }
    return byMunicipality
  }, [cases])

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-amber-800">Cobertura territorial</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Municipios</h1>
        <p className="mt-2 text-sm text-respira-muted">Municipios disponibles y sus registros históricos de IRA.</p>
      </div>
      {loading ? (
        <Card><Loading /></Card>
      ) : error ? (
        <Card><ErrorState message={error} /></Card>
      ) : municipalities.length === 0 ? (
        <Card><EmptyState /></Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">Municipio</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Departamento</th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">Casos registrados</th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">Última semana</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {municipalities.map((municipality) => {
                  const summary = totals.get(municipality.id)
                  return (
                    <tr key={municipality.id} className="hover:bg-slate-50/80">
                      <th scope="row" className="px-6 py-4 font-semibold text-respira-text">{municipality.name}</th>
                      <td className="px-6 py-4 text-respira-muted">{municipality.department}</td>
                      <td className="px-6 py-4 text-right tabular-nums">{(summary?.cases ?? 0).toLocaleString('es-CO')}</td>
                      <td className="px-6 py-4 text-right text-respira-muted">
                        {summary?.year ? `${summary.year} · S${summary.week}` : 'Sin registros'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
