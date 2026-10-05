import { useEffect, useState } from 'react'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { fetchCases } from '../services/caseService'
import type { IraCase } from '../types/case'

export function CasesPage() {
  const [cases, setCases] = useState<IraCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchCases({}, controller.signal)
      .then(setCases)
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

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-amber-800">Registros epidemiológicos</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Casos IRA</h1>
        <p className="mt-2 text-sm text-respira-muted">Consulta de casos por municipio y semana epidemiológica.</p>
      </div>
      {loading ? (
        <Card><Loading /></Card>
      ) : error ? (
        <Card><ErrorState message={error} /></Card>
      ) : cases.length === 0 ? (
        <Card><EmptyState /></Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">Año</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Semana epidemiológica</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Municipio (ID)</th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">Casos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cases.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-50/80">
                    <td className="px-6 py-3.5">{record.year}</td>
                    <td className="px-6 py-3.5">Semana {record.epidemiological_week}</td>
                    <td className="px-6 py-3.5 text-respira-muted">{record.municipality_id}</td>
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
