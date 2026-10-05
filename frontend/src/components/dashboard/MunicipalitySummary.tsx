import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { MunicipalitySummary as MunicipalitySummaryData } from '../../types/municipality'
import { Card } from '../common/Card'

interface MunicipalitySummaryProps {
  municipalities: MunicipalitySummaryData[]
}

export function MunicipalitySummary({ municipalities }: MunicipalitySummaryProps) {
  const entries = municipalities.slice(0, 5)
  const maximumCases = Math.max(...entries.map((municipality) => municipality.cases), 1)

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-respira-border px-5 py-5 sm:px-6">
        <div>
          <h2 className="font-semibold text-respira-text">Municipios monitoreados</h2>
          <p className="mt-1 text-xs text-respira-muted">Casos acumulados en el periodo disponible</p>
        </div>
        <Link
          to="/municipalities"
          className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 hover:text-amber-950"
        >
          Ver todos <ArrowUpRight size={15} aria-hidden="true" />
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="p-6 text-sm text-respira-muted">No hay datos disponibles.</p>
      ) : (
        <ul className="divide-y divide-slate-100 px-5 sm:px-6">
          {entries.map((municipality) => (
            <li key={municipality.id} className="flex items-center gap-4 py-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <span className="truncate text-sm font-medium text-respira-text">{municipality.name}</span>
                  <span className="text-sm font-semibold tabular-nums text-respira-text">
                    {municipality.cases.toLocaleString('es-CO')}
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-respira-yellow"
                    style={{ width: `${(municipality.cases / maximumCases) * 100}%` }}
                  />
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
