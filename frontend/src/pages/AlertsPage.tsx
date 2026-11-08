import { AlertTriangle, Bell, ChevronRight, Eye } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { RiskBadge } from '../components/common/RiskBadge'
import { useI18n } from '../i18n/I18nContext'
import { fetchAlerts } from '../services/riskService'
import type { AlertResponse, EpidemiologicalAlert } from '../types/risk'

function AlertRow({ alert }: { alert: EpidemiologicalAlert }) {
  const { t, language, locale } = useI18n()
  const high = alert.risk_level === 'high'
  const Icon = high ? AlertTriangle : Eye
  // El motivo llega redactado en español desde el servidor; en inglés se compone con las mismas cifras.
  const reason =
    language === 'en' ? t('alerts.reason', { week: alert.week, pct: alert.variation_percent }) : alert.reason
  return (
    <article className="grid gap-4 border-t border-respira-border px-5 py-5 first:border-t-0 md:grid-cols-[auto_minmax(0,1fr)_auto] md:items-center">
      <span
        className={`hidden h-12 w-12 items-center justify-center rounded-2xl md:flex ${
          high ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-800'
        }`}
      >
        <Icon size={22} aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-bold text-respira-text">{alert.municipality}</h2>
          <RiskBadge level={alert.risk_level} label={high ? t('risk.highFull') : t('risk.watch')} />
          <span className="text-xs text-respira-muted">
            {t('alerts.weekYear', { week: alert.week, year: alert.year })}
          </span>
        </div>
        <p className="mt-2 text-sm leading-6 text-respira-muted">{reason}</p>
        <p className="mt-1 text-xs text-respira-muted">{t('alerts.rule')}</p>
      </div>
      <div className="flex items-center justify-between gap-5 md:justify-end">
        <div className="text-right">
          <p className="text-2xl font-extrabold tabular-nums leading-none">
            {alert.observed_cases.toLocaleString(locale)}
          </p>
          <p className="mt-1 text-xs text-respira-muted">
            {t('alerts.casesAvg', { avg: alert.historical_average.toLocaleString(locale) })}
          </p>
          <p className={`text-xs font-bold ${high ? 'text-rose-700' : 'text-amber-800'}`}>
            {alert.variation_percent > 0 ? '+' : ''}
            {alert.variation_percent}%
          </p>
        </div>
        <Link
          className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-semibold text-sky-800 hover:bg-sky-100"
          to={`/municipalities/${alert.municipality_id}`}
        >
          {t('alerts.viewMunicipality')} <ChevronRight size={15} aria-hidden="true" />
        </Link>
      </div>
    </article>
  )
}

export function AlertsPage() {
  const { t } = useI18n()
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
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : t('alerts.loadError'))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, week])

  const all = data?.alerts ?? []
  const alerts = all.filter((item) => level === 'all' || item.risk_level === level)
  const highCount = all.filter((item) => item.risk_level === 'high').length

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('alerts.eyebrow')}
        title={t('alerts.title')}
        icon={Bell}
        description={t('alerts.description')}
      />
      <FilterBar
        note={t('common.period', {
          value: data?.year
            ? t('common.yearWeek', { year: data.year, week: data.week ?? '—' })
            : t('common.periodLatest'),
        })}
      >
        <FilterField label={t('common.year')}>
          <select
            className="field-control"
            value={year ?? ''}
            onChange={(event) => {
              setYear(event.target.value ? Number(event.target.value) : undefined)
              setWeek(undefined)
            }}
          >
            <option value="">{t('common.latest')}</option>
            {(data?.available_years ?? []).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('common.week')}>
          <select
            className="field-control"
            value={week ?? ''}
            onChange={(event) => setWeek(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">{t('common.latestAvailable')}</option>
            {Array.from({ length: 53 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('alerts.level')}>
          <select
            className="field-control"
            value={level}
            onChange={(event) => setLevel(event.target.value as typeof level)}
          >
            <option value="all">{t('common.all')}</option>
            <option value="moderate">{t('risk.watch')}</option>
            <option value="high">{t('risk.highFull')}</option>
          </select>
        </FilterField>
      </FilterBar>

      {loading ? (
        <Card>
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error} />
        </Card>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="inline-flex items-center gap-2 rounded-full bg-respira-surface px-4 py-2 font-semibold shadow-card">
              <Bell size={16} className="text-sky-800" aria-hidden="true" /> {t('alerts.count', { n: all.length })}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-rose-100 px-4 py-2 font-semibold text-rose-900">
              <AlertTriangle size={16} aria-hidden="true" /> {t('alerts.highCount', { n: highCount })}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-amber-100 px-4 py-2 font-semibold text-amber-950">
              <Eye size={16} aria-hidden="true" /> {t('alerts.watchCount', { n: all.length - highCount })}
            </span>
          </div>
          <Card className="overflow-hidden">
            {alerts.length ? (
              alerts.map((alert) => (
                <AlertRow key={`${alert.municipality_id}-${alert.year}-${alert.week}`} alert={alert} />
              ))
            ) : (
              <EmptyState>
                <span className="inline-flex items-center gap-2">
                  <AlertTriangle size={16} aria-hidden="true" /> {t('alerts.none')}
                </span>
              </EmptyState>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
