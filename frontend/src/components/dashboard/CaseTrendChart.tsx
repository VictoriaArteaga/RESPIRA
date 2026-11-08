import { TrendingDown, TrendingUp } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from 'recharts'
import { useI18n } from '../../i18n/I18nContext'
import type { IraCase } from '../../types/case'
import { Card } from '../common/Card'
import { EmptyState } from '../common/Feedback'

interface CaseTrendChartProps {
  cases: IraCase[]
}

interface Point {
  week: number
  cases: number
  previous?: number
  average: number
}

type Series = 'previous' | 'average' | 'mean'

const COLORS = { previous: '#94a3b8', average: '#d9a400', mean: '#7c8da0' }
const MOVING_WINDOW = 4

function weeklyTotals(cases: IraCase[], year: number): Map<number, number> {
  const totals = new Map<number, number>()
  for (const record of cases) {
    if (record.year !== year) continue
    totals.set(record.epidemiological_week, (totals.get(record.epidemiological_week) ?? 0) + record.cases)
  }
  return totals
}

function TrendTooltip({ active, payload, year }: TooltipProps<number, string> & { year: number }) {
  const { t, locale } = useI18n()
  const point = payload?.[0]?.payload as Point | undefined
  if (!active || !point) return null
  const delta = point.previous ? ((point.cases - point.previous) / point.previous) * 100 : null
  const rows: Array<[string, string, string]> = [
    [t('dash.trendCasesLabel', { year }), point.cases.toLocaleString(locale), 'var(--color-respira-blue)'],
    [t('dash.trendAvg'), point.average.toLocaleString(locale, { maximumFractionDigits: 1 }), COLORS.average],
  ]
  if (point.previous !== undefined) {
    rows.push([t('dash.trendPrevLabel', { year: year - 1 }), point.previous.toLocaleString(locale), COLORS.previous])
  }

  return (
    <div className="min-w-52 rounded-xl border border-respira-border bg-respira-surface px-3.5 py-3 text-xs shadow-[0_8px_24px_rgba(0,0,0,0.18)]">
      <p className="font-bold text-respira-text">{t('dash.trendTooltip', { week: point.week })}</p>
      <ul className="mt-2 space-y-1">
        {rows.map(([label, value, color]) => (
          <li key={label} className="flex items-center justify-between gap-4 text-respira-body">
            <span className="inline-flex items-center gap-2">
              <i className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {label}
            </span>
            <strong className="tabular-nums text-respira-text">{value}</strong>
          </li>
        ))}
      </ul>
      {delta !== null && (
        <p
          className={`mt-2 border-t border-respira-border pt-2 font-semibold ${delta > 0 ? 'text-rose-700' : 'text-emerald-800'}`}
        >
          {delta > 0 ? '+' : ''}
          {delta.toLocaleString(locale, { maximumFractionDigits: 1 })}% · {t('dash.trendPrev').toLowerCase()}
        </p>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-respira-border bg-respira-surface-alt px-4 py-3">
      <p className="text-xs text-respira-muted">{label}</p>
      <p className="mt-1 text-lg font-extrabold tabular-nums tracking-tight">{value}</p>
    </div>
  )
}

export function CaseTrendChart({ cases }: CaseTrendChartProps) {
  const { t, locale } = useI18n()
  const years = useMemo(() => [...new Set(cases.map((record) => record.year))].sort((a, b) => b - a), [cases])
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [hidden, setHidden] = useState<Set<Series>>(new Set())
  const year = selectedYear !== null && years.includes(selectedYear) ? selectedYear : (years[0] ?? 0)

  const data = useMemo<Point[]>(() => {
    const current = weeklyTotals(cases, year)
    const previous = weeklyTotals(cases, year - 1)
    const base = [...current.entries()].sort((a, b) => a[0] - b[0])
    return base.map(([week, total], index) => {
      const window = base.slice(Math.max(0, index - MOVING_WINDOW + 1), index + 1)
      return {
        week,
        cases: total,
        previous: previous.get(week),
        average: window.reduce((sum, [, value]) => sum + value, 0) / window.length,
      }
    })
  }, [cases, year])

  const hasPrevious = data.some((point) => point.previous !== undefined)
  const total = data.reduce((sum, point) => sum + point.cases, 0)
  const mean = data.length ? total / data.length : 0
  const peak = data.reduce<Point>((best, point) => (point.cases > best.cases ? point : best), {
    week: 0,
    cases: 0,
    average: 0,
  })

  // Variación acumulada frente al mismo tramo del año anterior (solo semanas con dato en ambos años).
  const comparable = data.filter((point) => point.previous !== undefined)
  const currentSum = comparable.reduce((sum, point) => sum + point.cases, 0)
  const previousSum = comparable.reduce((sum, point) => sum + (point.previous ?? 0), 0)
  const yoy = previousSum > 0 ? ((currentSum - previousSum) / previousSum) * 100 : null

  const toggle = (series: Series) =>
    setHidden((current) => {
      const next = new Set(current)
      if (next.has(series)) next.delete(series)
      else next.add(series)
      return next
    })

  const legend: Array<{ key: Series | null; label: string; swatch: ReactNode }> = [
    {
      key: null,
      label: t('dash.trendCasesLabel', { year }),
      swatch: <i className="h-1 w-5 rounded-full bg-respira-blue" />,
    },
    ...(hasPrevious
      ? [
          {
            key: 'previous' as const,
            label: t('dash.trendPrevLabel', { year: year - 1 }),
            swatch: <i className="h-0 w-5 border-t-2 border-dashed" style={{ borderColor: COLORS.previous }} />,
          },
        ]
      : []),
    {
      key: 'average' as const,
      label: t('dash.trendAvg'),
      swatch: <i className="h-1 w-5 rounded-full" style={{ backgroundColor: COLORS.average }} />,
    },
    {
      key: 'mean' as const,
      label: t('dash.trendMean'),
      swatch: <i className="h-0 w-5 border-t-2 border-dotted" style={{ borderColor: COLORS.mean }} />,
    },
  ]

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-respira-text">{t('dash.trendTitle')}</h2>
          <p className="mt-1 text-xs text-respira-muted">{t('dash.trendNote')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {yoy !== null && (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                yoy > 0 ? 'bg-rose-100 text-rose-900' : 'bg-emerald-100 text-emerald-900'
              }`}
            >
              {yoy > 0 ? <TrendingUp size={14} aria-hidden="true" /> : <TrendingDown size={14} aria-hidden="true" />}
              {t('dash.trendYoY', {
                pct: `${yoy > 0 ? '+' : ''}${yoy.toLocaleString(locale, { maximumFractionDigits: 1 })}`,
              })}
            </span>
          )}
          {years.length > 1 && (
            <label className="flex items-center gap-2 text-xs font-semibold text-respira-text">
              {t('common.year')}
              <select
                className="field-control min-h-9 py-0 text-xs"
                value={year}
                onChange={(event) => setSelectedYear(Number(event.target.value))}
              >
                {years.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </div>

      {data.length > 0 && (
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <Stat label={t('dash.trendTotal')} value={total.toLocaleString(locale)} />
          <Stat label={t('dash.trendMean')} value={mean.toLocaleString(locale, { maximumFractionDigits: 1 })} />
          <Stat
            label={t('dash.trendPeakStat')}
            value={`${peak.cases.toLocaleString(locale)} · ${t('dash.trendPeakLabel', { week: peak.week })}`}
          />
        </div>
      )}

      <ul className="mt-4 flex flex-wrap gap-2 text-xs">
        {legend.map(({ key, label, swatch }) => {
          const off = key !== null && hidden.has(key)
          return (
            <li key={label}>
              {key === null ? (
                <span className="inline-flex items-center gap-2 rounded-full border border-respira-border px-3 py-1.5 font-semibold text-respira-text">
                  {swatch}
                  {label}
                </span>
              ) : (
                <button
                  type="button"
                  aria-pressed={!off}
                  title={t('common.toggleSeries', { name: label })}
                  onClick={() => toggle(key)}
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-respira-blue-dark ${
                    off
                      ? 'border-respira-border text-respira-muted line-through opacity-60 hover:opacity-100'
                      : 'border-respira-border text-respira-text hover:bg-sky-50'
                  }`}
                >
                  {swatch}
                  {label}
                </button>
              )}
            </li>
          )
        })}
      </ul>

      {data.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="mt-4 h-[320px] w-full" role="img" aria-label={t('dash.trendAria')}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 20, right: 16, left: -12, bottom: 4 }}>
              <defs>
                <linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-respira-blue)" stopOpacity={0.34} />
                  <stop offset="100%" stopColor="var(--color-respira-blue)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--color-respira-border)" strokeDasharray="4 4" vertical={false} />
              <XAxis
                dataKey="week"
                tickLine={false}
                axisLine={false}
                tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
                tickFormatter={(week: number) => `S${week}`}
                minTickGap={22}
              />
              <YAxis
                allowDecimals={false}
                domain={[0, 'auto']}
                tickLine={false}
                axisLine={false}
                tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
              />
              <Tooltip
                cursor={{ stroke: 'var(--color-respira-muted)', strokeOpacity: 0.45, strokeWidth: 1 }}
                content={<TrendTooltip year={year} />}
              />
              {!hidden.has('mean') && (
                <ReferenceLine
                  y={mean}
                  stroke={COLORS.mean}
                  strokeDasharray="2 4"
                  strokeWidth={1.5}
                  ifOverflow="extendDomain"
                />
              )}
              {hasPrevious && !hidden.has('previous') && (
                <Line
                  type="monotone"
                  dataKey="previous"
                  stroke={COLORS.previous}
                  strokeWidth={1.75}
                  strokeDasharray="5 4"
                  dot={false}
                  activeDot={false}
                  isAnimationActive={false}
                />
              )}
              <Area
                type="monotone"
                dataKey="cases"
                stroke="var(--color-respira-blue)"
                strokeWidth={2.5}
                fill="url(#trend-fill)"
                activeDot={{
                  r: 5,
                  fill: 'var(--color-respira-blue)',
                  stroke: 'var(--color-respira-surface)',
                  strokeWidth: 2,
                }}
              />
              {!hidden.has('average') && (
                <Line
                  type="monotone"
                  dataKey="average"
                  stroke={COLORS.average}
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={false}
                />
              )}
              {peak.cases > 0 && (
                <ReferenceDot
                  x={peak.week}
                  y={peak.cases}
                  r={6}
                  fill={COLORS.average}
                  stroke="var(--color-respira-surface)"
                  strokeWidth={2.5}
                  ifOverflow="extendDomain"
                  label={{
                    value: t('dash.trendPeakLabel', { week: peak.week }),
                    position: 'top',
                    fill: 'var(--color-respira-text)',
                    fontSize: 11,
                    fontWeight: 700,
                  }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}
