import { Map as MapIcon, MousePointerClick } from 'lucide-react'
import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet'
import { Card } from '../components/common/Card'
import { DataBadge } from '../components/common/DataBadge'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { RiskBadge, riskMeta } from '../components/common/RiskBadge'
import { useI18n } from '../i18n/I18nContext'
import { fetchRiskMap } from '../services/riskService'
import type { MunicipalityRisk, RiskLevel, RiskMap } from '../types/risk'

function FitMunicipalities({ items }: { items: MunicipalityRisk[] }) {
  const map = useMap()
  useEffect(() => {
    if (items.length)
      map.fitBounds(
        items.map((item) => [item.latitude, item.longitude]),
        { padding: [36, 36] },
      )
  }, [items, map])
  return null
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-respira-border bg-respira-surface-alt p-3">
      <p className="text-xs text-respira-muted">{label}</p>
      <p className="mt-1 text-lg font-bold tabular-nums">{value}</p>
    </div>
  )
}

export function RiskMapPage() {
  const { t, locale } = useI18n()
  const [data, setData] = useState<RiskMap | null>(null)
  const [selected, setSelected] = useState<MunicipalityRisk | null>(null)
  const [year, setYear] = useState<number | undefined>()
  const [week, setWeek] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchRiskMap(year, week, controller.signal)
      .then((result) => {
        setData(result)
        setSelected(
          (current) => result.municipalities.find((item) => item.municipality_id === current?.municipality_id) ?? null,
        )
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : t('map.loadError'))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, week])

  const counts = (data?.municipalities ?? []).reduce<Record<RiskLevel, number>>(
    (totals, item) => ({ ...totals, [item.risk_level]: totals[item.risk_level] + 1 }),
    { low: 0, moderate: 0, high: 0, no_data: 0 },
  )

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('map.eyebrow')}
        title={t('map.title')}
        icon={MapIcon}
        description={t('map.description')}
        actions={<DataBadge />}
      />
      <FilterBar
        note={
          data?.year
            ? t('common.period', { value: t('common.yearWeek', { year: data.year, week: data.week ?? '—' }) })
            : undefined
        }
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
              <option key={value}>{value}</option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('map.epiWeek')}>
          <select
            className="field-control"
            value={week ?? ''}
            onChange={(event) => setWeek(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">{t('common.latestAvailable')}</option>
            {Array.from({ length: 53 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>
                {t('common.weekN', { n: value })}
              </option>
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
      ) : !data?.municipalities.length ? (
        <Card>
          <EmptyState>{t('common.noFilterData')}</EmptyState>
        </Card>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_minmax(300px,0.8fr)]">
          <Card className="overflow-hidden">
            <div className="flex flex-wrap gap-2 border-b border-respira-border px-5 py-4">
              {(['low', 'moderate', 'high', 'no_data'] as RiskLevel[]).map((level) => (
                <span
                  key={level}
                  className="inline-flex items-center gap-2 rounded-full bg-respira-surface-alt px-3 py-1 text-xs font-semibold"
                >
                  <i className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: riskMeta[level].color }} />
                  {t(riskMeta[level].label)}
                  <span className="text-respira-muted">· {counts[level]}</span>
                </span>
              ))}
            </div>
            <MapContainer center={[1.3, -78]} zoom={8} scrollWheelZoom className="h-[520px] w-full">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <FitMunicipalities items={data.municipalities} />
              {data.municipalities.map((item) => (
                <CircleMarker
                  key={item.municipality_id}
                  center={[item.latitude, item.longitude]}
                  radius={selected?.municipality_id === item.municipality_id ? 14 : 10}
                  pathOptions={{
                    color: '#fff',
                    weight: 2.5,
                    fillColor: riskMeta[item.risk_level].color,
                    fillOpacity: 0.92,
                  }}
                  eventHandlers={{ click: () => setSelected(item) }}
                >
                  <Tooltip>
                    {t('map.tooltip', {
                      name: item.municipality,
                      level: t(riskMeta[item.risk_level].label).toLowerCase(),
                    })}
                  </Tooltip>
                </CircleMarker>
              ))}
            </MapContainer>
          </Card>

          <Card className="p-5 sm:p-6">
            {selected ? (
              <>
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-respira-muted">
                  {selected.department} · {t('common.weekN', { n: selected.week ?? data.week ?? '—' })},{' '}
                  {selected.year ?? data.year}
                </p>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-xl font-extrabold">{selected.municipality}</h2>
                  <RiskBadge level={selected.risk_level} />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <Metric
                    label={t('det.observed')}
                    value={selected.current_cases?.toLocaleString(locale) ?? t('common.noDataShort')}
                  />
                  <Metric
                    label={t('det.historicalAvg')}
                    value={selected.historical_average?.toLocaleString(locale) ?? '—'}
                  />
                  <Metric
                    label={t('det.variation')}
                    value={
                      selected.variation_percent === null
                        ? '—'
                        : `${selected.variation_percent > 0 ? '+' : ''}${selected.variation_percent}%`
                    }
                  />
                  <Metric label={t('map.level')} value={t(riskMeta[selected.risk_level].label)} />
                </div>
                <p className="mt-5 text-xs leading-5 text-respira-muted">{t('map.disclaimer')}</p>
              </>
            ) : (
              <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-6 text-center text-sm text-respira-muted">
                <MousePointerClick size={22} aria-hidden="true" />
                {t('map.select')}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
