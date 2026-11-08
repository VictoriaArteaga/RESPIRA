import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  ChartNoAxesCombined,
  MapPinned,
  UsersRound,
  Wind,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { DataBadge } from '../components/common/DataBadge'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { CaseTrendChart } from '../components/dashboard/CaseTrendChart'
import { MunicipalitySummary } from '../components/dashboard/MunicipalitySummary'
import { RecentData } from '../components/dashboard/RecentData'
import { StatCard } from '../components/dashboard/StatCard'
import { useDashboard } from '../hooks/useDashboard'
import { useI18n } from '../i18n/I18nContext'
import { fetchAlerts } from '../services/riskService'
import type { MunicipalitySummary as MunicipalitySummaryData } from '../types/municipality'
import type { AlertResponse } from '../types/risk'

export function DashboardPage() {
  const { t, locale } = useI18n()
  const { data, loading, error } = useDashboard()
  const [alertData, setAlertData] = useState<AlertResponse | null>(null)
  const [alertsUnavailable, setAlertsUnavailable] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    fetchAlerts(undefined, undefined, controller.signal)
      .then(setAlertData)
      .catch(() => {
        if (!controller.signal.aborted) setAlertsUnavailable(true)
      })
    return () => controller.abort()
  }, [])

  const municipalitySummaries = useMemo<MunicipalitySummaryData[]>(() => {
    if (!data) return []

    const summaries = new Map<number, MunicipalitySummaryData>()
    for (const municipality of data.municipalities) {
      summaries.set(municipality.id, { ...municipality, cases: 0, latestYear: null, latestWeek: null })
    }
    for (const record of data.cases) {
      const municipality = summaries.get(record.municipality_id)
      if (!municipality) continue
      municipality.cases += record.cases
      if (
        municipality.latestYear === null ||
        record.year > municipality.latestYear ||
        (record.year === municipality.latestYear && record.epidemiological_week > (municipality.latestWeek ?? 0))
      ) {
        municipality.latestYear = record.year
        municipality.latestWeek = record.epidemiological_week
      }
    }

    return [...summaries.values()].sort((left, right) => right.cases - left.cases)
  }, [data])

  const highAlerts = alertData?.alerts.filter((alert) => alert.risk_level === 'high').length

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow={t('dash.eyebrow')}
        title={t('dash.title')}
        icon={ChartNoAxesCombined}
        description={t('dash.description')}
        actions={<DataBadge />}
      />

      {loading ? (
        <Card className="p-4">
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error} />
        </Card>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label={t('dash.totalCases')}
              value={data.summary.total_cases.toLocaleString(locale)}
              supportingText={t('dash.totalCasesNote')}
              icon={Activity}
              tone="blue"
            />
            <StatCard
              label={t('dash.municipalities')}
              value={data.summary.total_municipalities.toLocaleString(locale)}
              supportingText={t('dash.municipalitiesNote')}
              icon={MapPinned}
              tone="green"
            />
            <StatCard
              label={t('dash.average')}
              value={data.summary.average_cases.toLocaleString(locale, { maximumFractionDigits: 1 })}
              supportingText={t('dash.averageNote')}
              icon={UsersRound}
              tone="blue"
            />
            <StatCard
              label={t('dash.mostCases')}
              value={data.summary.municipality_with_most_cases ?? t('common.noRecords')}
              supportingText={t('dash.mostCasesNote')}
              icon={Wind}
              tone="amber"
            />
          </div>

          <section aria-label={t('dash.alertsSection')} className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label={t('dash.inWatch')}
              value={alertsUnavailable ? t('dash.unavailable') : String(alertData?.alerts.length ?? '—')}
              supportingText={t('dash.inWatchNote')}
              icon={Bell}
              tone="amber"
            />
            <StatCard
              label={t('dash.highRisk')}
              value={alertsUnavailable ? t('dash.unavailable') : String(highAlerts ?? '—')}
              supportingText={t('dash.highRiskNote')}
              icon={AlertTriangle}
              tone="rose"
            />
            <Card className="flex items-center justify-between gap-3 p-5 sm:p-6">
              <div>
                <p className="text-sm font-medium text-respira-muted">{t('dash.lastWeekSet')}</p>
                <p className="mt-3 text-3xl font-extrabold tracking-tight">
                  {data.summary.last_epidemiological_week
                    ? t('common.weekN', { n: data.summary.last_epidemiological_week })
                    : t('common.noRecords')}
                </p>
              </div>
              <Link
                to="/alerts"
                className="inline-flex items-center gap-1 rounded-xl bg-sky-100/80 px-3 py-2 text-sm font-semibold text-sky-900 hover:bg-sky-100"
              >
                {t('dash.viewAlerts')} <ArrowUpRight size={15} aria-hidden="true" />
              </Link>
            </Card>
          </section>

          {data.summary.total_records === 0 ? (
            <Card>
              <EmptyState />
            </Card>
          ) : (
            <>
              <section aria-label={t('dash.chartSection')}>
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
