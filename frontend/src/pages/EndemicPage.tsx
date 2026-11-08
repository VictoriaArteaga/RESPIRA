import { Activity, ChartLine, Gauge, TrendingUp, Waves } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '../components/common/Card'
import { DataBadge } from '../components/common/DataBadge'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { RiskBadge } from '../components/common/RiskBadge'
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

  const legend = [
    [t('endemic.observed'), '#c83d3d'],
    [t('endemic.medianHist'), 'var(--color-respira-blue)'],
    [t('endemic.p2575'), '#94a3b8'],
    [t('endemic.p90'), '#d9a400'],
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('endemic.eyebrow')}
        title={t('endemic.title')}
        icon={ChartLine}
        description={t('endemic.description')}
        actions={<DataBadge />}
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

          <Card className="p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-bold">
                  {data.municipality} · {data.year}
                </h2>
                <p className="mt-1 text-xs text-respira-muted">{t('endemic.chartNote')}</p>
              </div>
              <ul className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-respira-muted">
                {legend.map(([label, color]) => (
                  <li key={label} className="inline-flex items-center gap-2">
                    <i className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                    {label}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-5 h-[420px] w-full" role="img" aria-label={t('endemic.chartAria')}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.weeks} margin={{ top: 12, right: 20, bottom: 8, left: -8 }}>
                  <CartesianGrid strokeDasharray="4 4" stroke="var(--color-respira-border)" vertical={false} />
                  <XAxis
                    dataKey="week"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
                    tickFormatter={(week: number) => `S${week}`}
                    minTickGap={20}
                  />
                  <YAxis
                    allowDecimals={false}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
                  />
                  <Tooltip
                    cursor={{ stroke: 'var(--color-respira-muted)', strokeOpacity: 0.45, strokeWidth: 1 }}
                    labelFormatter={(value) => t('common.weekN', { n: String(value) })}
                    formatter={(value, name) => [value ?? t('endemic.noHistory'), name]}
                    contentStyle={{
                      border: '1px solid var(--color-respira-border)',
                      background: 'var(--color-respira-surface)',
                      color: 'var(--color-respira-text)',
                      borderRadius: '12px',
                      boxShadow: '0 8px 24px rgba(36,59,74,0.10)',
                      fontSize: '12px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="upper_alert_limit"
                    name={t('endemic.p90')}
                    stroke="#d9a400"
                    strokeDasharray="5 4"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="upper_limit"
                    name={t('endemic.p75')}
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="historical_median"
                    name={t('endemic.medianHist')}
                    stroke="var(--color-respira-blue)"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="lower_limit"
                    name={t('endemic.p25')}
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="observed_cases"
                    name={t('endemic.observed')}
                    stroke="#c83d3d"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-respira-muted">{t('endemic.footnote')}</p>
          </Card>
        </>
      )}
    </div>
  )
}
