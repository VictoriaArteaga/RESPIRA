import { Activity, ChartLine, Gauge, TrendingUp, Waves } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { RiskBadge } from '../components/common/RiskBadge'
import { EndemicChart } from '../components/endemic/EndemicChart'
import { StatCard } from '../components/dashboard/StatCard'
import { useI18n } from '../i18n/I18nContext'
import { fetchMunicipalities } from '../services/municipalityService'
import { fetchEndemicChannel } from '../services/riskService'
import type { Municipality } from '../types/municipality'
import type { EndemicChannel } from '../types/risk'

export function EndemicPage() {
  const { t, locale } = useI18n()
  const [municipalities, setMunicipalities] = useState<Municipality[]>([])
  const [municipalityId, setMunicipalityId] = useState<number | undefined>()
  const [year, setYear] = useState<number | undefined>()
  const [data, setData] = useState<EndemicChannel | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fail = (reason: unknown) => (reason instanceof Error ? reason.message : t('map.loadError'))
  const number = (value: number | undefined) => (value === undefined ? '—' : value.toLocaleString(locale))

  useEffect(() => {
    const controller = new AbortController()
    fetchMunicipalities(controller.signal)
      .then((values) => {
        setMunicipalities(values)
        setMunicipalityId((current) => current ?? values[0]?.id)
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(fail(reason))
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!municipalityId) return
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchEndemicChannel(municipalityId, year, controller.signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(fail(reason))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipalityId, year])

  const stats = data?.statistics

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('endemic.eyebrow')}
        title={t('endemic.title')}
        icon={ChartLine}
        description={t('endemic.description')}
      />
      <FilterBar>
        <FilterField label={t('common.municipality')}>
          <select
            className="field-control min-w-52"
            value={municipalityId ?? ''}
            onChange={(event) => setMunicipalityId(Number(event.target.value))}
          >
            {municipalities.map((municipality) => (
              <option key={municipality.id} value={municipality.id}>
                {municipality.name}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('common.year')}>
          <select
            className="field-control"
            value={year ?? ''}
            onChange={(event) => setYear(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">{t('common.latest')}</option>
            {(data?.available_years ?? []).map((value) => (
              <option key={value}>{value}</option>
            ))}
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
      ) : !data?.weeks.length ? (
        <Card>
          <EmptyState>{t('common.noFilterData')}</EmptyState>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label={t('endemic.periodCases')}
              value={number(stats?.total_cases)}
              supportingText={t('endemic.periodCasesNote')}
              icon={Activity}
              tone="blue"
            />
            <StatCard
              label={t('endemic.weeklyAvg')}
              value={number(stats?.average)}
              supportingText={t('endemic.median', { value: number(stats?.median) })}
              icon={Waves}
              tone="green"
            />
            <StatCard
              label={t('endemic.weeklyMax')}
              value={number(stats?.maximum)}
              supportingText={t('endemic.min', { value: number(stats?.minimum) })}
              icon={TrendingUp}
              tone="amber"
            />
            <Card className="relative overflow-hidden p-5 sm:p-6">
              <span className="absolute inset-x-0 top-0 h-1 bg-respira-blue" aria-hidden="true" />
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-respira-muted">{t('endemic.currentRisk')}</p>
                  <div className="mt-3">
                    <RiskBadge level={stats?.risk_level ?? 'no_data'} />
                  </div>
                  <p className="mt-3 text-xs text-respira-muted">
                    {t('common.weekN', { n: stats?.latest_week ?? '—' })}
                  </p>
                </div>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
                  <Gauge size={20} aria-hidden="true" />
                </span>
              </div>
            </Card>
          </div>

          <EndemicChart data={data} />
        </>
      )}
    </div>
  )
}
