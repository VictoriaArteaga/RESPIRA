import { Activity, ArrowLeft, CalendarDays, CloudRain, Droplets, Gauge, Thermometer, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { RiskBadge } from '../components/common/RiskBadge'
import { CaseTrendChart } from '../components/dashboard/CaseTrendChart'
import { StatCard } from '../components/dashboard/StatCard'
import { useI18n } from '../i18n/I18nContext'
import { fetchCases } from '../services/caseService'
import { fetchMunicipality } from '../services/municipalityService'
import { fetchEndemicChannel, fetchMunicipalityRisk } from '../services/riskService'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'
import type { EndemicChannel, MunicipalityRisk } from '../types/risk'

const byLatest = (a: IraCase, b: IraCase) => b.year - a.year || b.epidemiological_week - a.epidemiological_week

export function MunicipalityDetailPage() {
  const { t, locale } = useI18n()
  const { id } = useParams()
  const municipalityId = Number(id)
  const [municipality, setMunicipality] = useState<Municipality | null>(null)
  const [cases, setCases] = useState<IraCase[]>([])
  const [risk, setRisk] = useState<MunicipalityRisk | null>(null)
  const [channel, setChannel] = useState<EndemicChannel | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    if (!Number.isInteger(municipalityId) || municipalityId < 1) {
      setError(t('det.invalidId'))
      setLoading(false)
      return () => controller.abort()
    }
    setLoading(true)
    setError(null)
    Promise.all([
      fetchMunicipality(municipalityId, controller.signal),
      fetchCases({ municipality_id: municipalityId }, controller.signal),
    ])
      .then(async ([municipalityData, caseData]) => {
        setMunicipality(municipalityData)
        setCases(caseData)
        const latest = [...caseData].sort(byLatest)[0]
        if (latest) {
          const [riskData, channelData] = await Promise.all([
            fetchMunicipalityRisk(municipalityId, latest.year, latest.epidemiological_week, controller.signal),
            fetchEndemicChannel(municipalityId, latest.year, controller.signal),
          ])
          setRisk(riskData)
          setChannel(channelData)
        }
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : t('det.loadError'))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipalityId])

  const latest = [...cases].sort(byLatest)[0]
  const total = cases.reduce((sum, item) => sum + item.cases, 0)

  return (
    <div className="space-y-6">
      <Link
        to="/municipalities"
        className="inline-flex items-center gap-2 rounded-lg px-2 py-1 text-sm font-semibold text-sky-800 hover:bg-sky-100"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        {t('det.back')}
      </Link>
      {loading ? (
        <Card>
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error} />
        </Card>
      ) : !municipality ? (
        <Card>
          <EmptyState />
        </Card>
      ) : (
        <>
          <PageHeader
            eyebrow={t('det.eyebrow', { department: municipality.department })}
            title={municipality.name}
            description={t('det.description')}
          />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label={t('det.totalCases')}
              value={total.toLocaleString(locale)}
              supportingText={t('det.totalCasesNote')}
              icon={Activity}
              tone="blue"
            />
            <StatCard
              label={t('det.lastPeriod')}
              value={latest ? t('common.weekN', { n: latest.epidemiological_week }) : t('common.noRecords')}
              supportingText={latest ? String(latest.year) : t('common.noRecords')}
              icon={CalendarDays}
              tone="green"
            />
            <Card className="relative overflow-hidden p-5 sm:p-6">
              <span className="absolute inset-x-0 top-0 h-1 bg-amber-500" aria-hidden="true" />
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-respira-muted">{t('det.risk')}</p>
                  <div className="mt-3">
                    <RiskBadge level={risk?.risk_level ?? 'no_data'} />
                  </div>
                  <p className="mt-3 text-xs text-respira-muted">{t('det.riskNote')}</p>
                </div>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
                  <Gauge size={20} aria-hidden="true" />
                </span>
              </div>
            </Card>
            <StatCard
              label={t('det.channelWeeks')}
              value={String(channel?.weeks.length ?? 0)}
              supportingText={t('det.channelWeeksNote')}
              icon={TrendingUp}
              tone="amber"
            />
          </div>

          {!cases.length ? (
            <Card>
              <EmptyState>{t('det.noCases')}</EmptyState>
            </Card>
          ) : (
            <>
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
                <CaseTrendChart cases={cases} />
                <Card className="p-5 sm:p-6">
                  <h2 className="font-bold">{t('det.riskTitle')}</h2>
                  <p className="mt-1 text-sm text-respira-muted">
                    {t('common.yearWeek', { year: risk?.year ?? '—', week: risk?.week ?? '—' })}
                  </p>
                  <dl className="mt-5 divide-y divide-respira-border text-sm">
                    <div className="flex justify-between gap-3 py-3">
                      <dt className="text-respira-muted">{t('det.observed')}</dt>
                      <dd className="font-bold tabular-nums">{risk?.current_cases ?? t('common.noDataShort')}</dd>
                    </div>
                    <div className="flex justify-between gap-3 py-3">
                      <dt className="text-respira-muted">{t('det.historicalAvg')}</dt>
                      <dd className="font-bold tabular-nums">{risk?.historical_average ?? t('common.noReference')}</dd>
                    </div>
                    <div className="flex justify-between gap-3 py-3">
                      <dt className="text-respira-muted">{t('det.variation')}</dt>
                      <dd className="font-bold tabular-nums">
                        {risk?.variation_percent == null
                          ? '—'
                          : `${risk.variation_percent > 0 ? '+' : ''}${risk.variation_percent}%`}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-2 text-xs leading-5 text-respira-muted">{t('det.riskDisclaimer')}</p>
                  <Link to="/alerts" className="mt-4 inline-block text-sm font-semibold text-sky-800 hover:underline">
                    {t('det.viewAlerts')}
                  </Link>
                </Card>
              </div>

              {latest && (
                <Card className="p-5 sm:p-6">
                  <h2 className="font-bold">{t('det.varsTitle')}</h2>
                  <p className="mt-1 text-xs text-respira-muted">
                    {t('det.varsNote', { year: latest.year, week: latest.epidemiological_week })}
                  </p>
                  <dl className="mt-5 grid gap-4 sm:grid-cols-3">
                    {[
                      { label: t('det.temperature'), value: latest.temperature === null ? '—' : `${latest.temperature} °C`, icon: Thermometer },
                      { label: t('det.precipitation'), value: latest.precipitation === null ? '—' : `${latest.precipitation} mm`, icon: CloudRain },
                      { label: t('det.humidity'), value: latest.humidity === null ? '—' : `${latest.humidity}%`, icon: Droplets },
                    ].map(({ label, value, icon: Icon }) => (
                      <div
                        key={label}
                        className="flex items-center gap-3 rounded-xl border border-respira-border bg-respira-surface-alt p-4"
                      >
                        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-100 text-sky-800">
                          <Icon size={19} aria-hidden="true" />
                        </span>
                        <div>
                          <dt className="text-xs text-respira-muted">{label}</dt>
                          <dd className="mt-0.5 text-lg font-bold">{value}</dd>
                        </div>
                      </div>
                    ))}
                  </dl>
                </Card>
              )}

              <Card className="p-5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="font-bold">{t('det.channelTitle')}</h2>
                    <p className="mt-1 text-xs text-respira-muted">
                      {t('det.channelNote', {
                        count: channel?.weeks.length ?? 0,
                        year: channel?.year ?? t('det.channelNotePeriod'),
                      })}
                    </p>
                  </div>
                  <Link
                    to="/endemic"
                    className="rounded-xl bg-sky-100/80 px-4 py-2 text-sm font-semibold text-sky-900 hover:bg-sky-100"
                  >
                    {t('det.openChannel')}
                  </Link>
                </div>
                <p className="mt-3 text-sm text-respira-muted">{t('det.channelText')}</p>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  )
}
