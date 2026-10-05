import { Activity, MapPinned, UsersRound, Wind } from 'lucide-react'
import { useMemo } from 'react'
import { Badge } from '../components/common/Badge'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { MunicipalitySummary } from '../components/dashboard/MunicipalitySummary'
import { RecentData } from '../components/dashboard/RecentData'
import { StatCard } from '../components/dashboard/StatCard'
import { CaseTrendChart } from '../components/dashboard/CaseTrendChart'
import { useDashboard } from '../hooks/useDashboard'
import type { MunicipalitySummary as MunicipalitySummaryData } from '../types/municipality'

export function DashboardPage() {
  const { data, loading, error } = useDashboard()
  const municipalitySummaries = useMemo<MunicipalitySummaryData[]>(() => {
    if (!data) return []

    const summaries = new Map<number, MunicipalitySummaryData>()
    for (const municipality of data.municipalities) {
      summaries.set(municipality.id, {
        ...municipality,
        cases: 0,
        latestYear: null,
        latestWeek: null,
      })
    }
    for (const record of data.cases) {
      const municipality = summaries.get(record.municipality_id)
      if (!municipality) continue
      municipality.cases += record.cases
      if (
        municipality.latestYear === null ||
        record.year > municipality.latestYear ||
        (record.year === municipality.latestYear &&
          record.epidemiological_week > (municipality.latestWeek ?? 0))
      ) {
        municipality.latestYear = record.year
        municipality.latestWeek = record.epidemiological_week
      }
    }

    return [...summaries.values()].sort((left, right) => right.cases - left.cases)
  }, [data])

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-amber-800">Panel de seguimiento</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-respira-text sm:text-3xl">
            Dashboard
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-respira-muted">
            Resumen de los registros de infecciones respiratorias agudas en los municipios de Nariño.
          </p>
        </div>
        <Badge className="border border-amber-200 bg-white">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-600" />
          Datos sintéticos — versión de desarrollo
        </Badge>
      </div>

      {loading ? (
        <Card className="p-4">
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error || 'No fue posible obtener la información del servidor.'} />
        </Card>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Total de casos IRA"
              value={data.summary.total_cases.toLocaleString('es-CO')}
              supportingText="Casos registrados en el periodo"
              icon={Activity}
            />
            <StatCard
              label="Municipios monitoreados"
              value={data.summary.total_municipalities.toLocaleString('es-CO')}
              supportingText="Municipios disponibles en Nariño"
              icon={MapPinned}
            />
            <StatCard
              label="Promedio de casos"
              value={data.summary.average_cases.toLocaleString('es-CO', {
                maximumFractionDigits: 1,
              })}
              supportingText="Promedio acumulado por municipio"
              icon={UsersRound}
            />
            <StatCard
              label="Mayor número de casos"
              value={data.summary.municipality_with_most_cases ?? 'Sin registros'}
              supportingText="Municipio con más casos acumulados"
              icon={Wind}
            />
          </div>

          {data.summary.total_records === 0 ? (
            <Card>
              <EmptyState />
            </Card>
          ) : (
            <>
              <section aria-label="Gráfica de tendencia y municipios">
                <div className="grid gap-5 xl:grid-cols-[minmax(0,1.65fr)_minmax(300px,1fr)]">
                  <CaseTrendChart cases={data.cases} />
                  <MunicipalitySummary municipalities={municipalitySummaries} />
                </div>
              </section>
              <RecentData
                summary={data.summary}
                period={
                  data.cases.length > 0
                    ? `${Math.min(...data.cases.map((record) => record.year))} – ${Math.max(...data.cases.map((record) => record.year))}`
                    : null
                }
              />
            </>
          )}
        </>
      ) : (
        <Card>
          <EmptyState />
        </Card>
      )}
    </div>
  )
}
