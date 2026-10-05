import { CalendarDays, Database, MapPin, TrendingUp } from 'lucide-react'
import type { DashboardSummary } from '../../types/dashboard'
import { Card } from '../common/Card'

interface RecentDataProps {
  summary: DashboardSummary
  period: string | null
}

export function RecentData({ summary, period }: RecentDataProps) {
  const items = [
    {
      label: 'Última semana disponible',
      value: summary.last_epidemiological_week
        ? `Semana ${summary.last_epidemiological_week}`
        : 'Sin registros',
      icon: CalendarDays,
    },
    {
      label: 'Registros disponibles',
      value: summary.total_records.toLocaleString('es-CO'),
      icon: Database,
    },
    {
      label: 'Municipio con más casos',
      value: summary.municipality_with_most_cases ?? 'Sin registros',
      icon: MapPin,
    },
    {
      label: 'Periodo de datos',
      value: period ?? 'Sin registros',
      icon: TrendingUp,
    },
  ]

  return (
    <Card className="p-5 sm:p-6">
      <div className="mb-5">
        <h2 className="font-semibold text-respira-text">Resumen de monitoreo</h2>
        <p className="mt-1 text-xs text-respira-muted">Cobertura del conjunto de datos disponible</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-start gap-3 rounded-xl bg-slate-50 p-4">
            <Icon size={18} className="mt-0.5 shrink-0 text-amber-800" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-xs text-respira-muted">{label}</p>
              <p className="mt-1 truncate text-sm font-semibold text-respira-text">{value}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
