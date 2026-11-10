import { useId, useState } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from 'recharts'
import { useI18n } from '../../i18n/I18nContext'
import { usePreferences } from '../../preferences/PreferencesContext'
import type { ForecastResult } from '../../types/forecast'
import { Card } from '../common/Card'

// Los colores salen de variables CSS para que la gráfica se lea igual en modo claro y oscuro.
const COLORS = {
  history: 'var(--color-respira-link)',
  predicted: 'var(--forecast-line)',
  observed: '#e04f4f',
  surface: 'var(--color-respira-surface)',
}

// Periodos del historial. "Todo" muestra desde 2012; los demás acercan la gráfica para ver de cerca la estimación,
// que en la vista completa queda al borde derecho.
const RANGES = [
  { id: 'all', weeks: Infinity, label: 'fc.rangeAll' },
  { id: '5y', weeks: 260, label: 'fc.range5y' },
  { id: '2y', weeks: 104, label: 'fc.range2y' },
  { id: '1y', weeks: 52, label: 'fc.range1y' },
  { id: '26w', weeks: 26, label: 'fc.range26w' },
] as const
type RangeId = (typeof RANGES)[number]['id']
// Con más de esta cantidad de semanas el eje muestra un año por marca en vez de "S12", "S13"...
const YEAR_TICKS_FROM_WEEKS = 80

interface Row {
  key: string
  label: string
  year: number
  week: number | null
  cases: number | null
  predicted: number | null
  band: [number, number] | null
  observedLater: number | null
  isPrediction: boolean
  // Semana intermedia sin estimación propia: solo une la última semana con dato con la primera estimación.
  isGap: boolean
}

function buildRows(data: ForecastResult, visibleWeeks: number): Row[] {
  const history = Number.isFinite(visibleWeeks) ? data.history.slice(-visibleWeeks) : data.history
  const rows: Row[] = history.map((point) => ({
    key: `${point.year}-${point.week}`,
    label: `S${point.week}`,
    year: point.year,
    week: point.week,
    cases: point.cases,
    predicted: null,
    band: null,
    observedLater: null,
    isPrediction: false,
    isGap: false,
  }))
  // La estimación parte del último valor observado para que se lea como continuación de la línea.
  const last = rows[rows.length - 1]
  if (last) {
    last.predicted = last.cases
    if (last.cases !== null) last.band = [last.cases, last.cases]
  }

  const sorted = [...data.predictions].sort((a, b) => a.horizon_weeks - b.horizon_weeks)
  let previous = { horizon: 0, value: last?.cases ?? null, low: last?.cases ?? null, high: last?.cases ?? null }
  for (const p of sorted) {
    // Semanas entre la última con dato y la primera estimación (p. ej. la semana 41): se interpolan para no
    // comprimir el eje y mostrar la distancia real.
    for (let h = previous.horizon + 1; h < p.horizon_weeks; h++) {
      const ratio = (h - previous.horizon) / (p.horizon_weeks - previous.horizon)
      const lerp = (from: number | null, to: number) => (from === null ? to : from + (to - from) * ratio)
      const gapWeek = p.target_week - (p.horizon_weeks - h)
      rows.push({
        key: `gap-${h}`,
        label: gapWeek >= 1 ? `S${gapWeek}` : '',
        year: p.target_year,
        week: gapWeek >= 1 ? gapWeek : null,
        cases: null,
        predicted: lerp(previous.value, p.predicted_cases),
        band: [lerp(previous.low, p.interval_low), lerp(previous.high, p.interval_high)],
        observedLater: null,
        isPrediction: false,
        isGap: true,
      })
    }
    rows.push({
      key: `${p.target_year}-${p.target_week}`,
      label: `S${p.target_week}`,
      year: p.target_year,
      week: p.target_week,
      cases: null,
      predicted: p.predicted_cases,
      band: [p.interval_low, p.interval_high],
      observedLater: p.observed_cases,
      isPrediction: true,
      isGap: false,
    })
    previous = { horizon: p.horizon_weeks, value: p.predicted_cases, low: p.interval_low, high: p.interval_high }
  }
  return rows
}

function niceDomain(rows: Row[]): [number, number] {
  const values: number[] = []
  for (const row of rows) {
    if (row.cases !== null) values.push(row.cases)
    if (row.band) values.push(row.band[0], row.band[1])
    if (row.observedLater !== null) values.push(row.observedLater)
  }
  if (!values.length) return [0, 10]
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.12, 2)
  const step = max - min > 100 ? 10 : 5
  return [Math.max(0, Math.floor((min - pad) / step) * step), Math.ceil((max + pad) / step) * step]
}

function ForecastTooltip({ active, payload }: TooltipProps<number, string>) {
  const { t, locale } = useI18n()
  const row = payload?.[0]?.payload as Row | undefined
  if (!active || !row || row.isGap || row.week === null) return null
  const n = (value: number | null) => (value === null ? '—' : value.toLocaleString(locale, { maximumFractionDigits: 1 }))
  return (
    <div className="min-w-52 rounded-xl border border-respira-border bg-respira-surface px-3.5 py-3 text-xs shadow-[0_8px_24px_rgba(0,0,0,0.18)]">
      <p className="font-bold text-respira-text">{t('fc.weekOfYear', { week: row.week, year: row.year })}</p>
      <ul className="mt-2 space-y-1 border-t border-respira-border pt-2 text-respira-body">
        {row.cases !== null && (
          <li className="flex justify-between gap-4">
            <span>{t('fc.legendHistory')}</span>
            <strong className="tabular-nums text-respira-text">{n(row.cases)}</strong>
          </li>
        )}
        {row.isPrediction && (
          <>
            <li className="flex justify-between gap-4">
              <span>{t('fc.legendPredicted')}</span>
              <strong className="tabular-nums text-respira-text">{n(row.predicted)}</strong>
            </li>
            <li className="flex justify-between gap-4">
              <span>{t('fc.legendBand')}</span>
              <strong className="tabular-nums text-respira-text">
                {row.band ? `${n(row.band[0])} – ${n(row.band[1])}` : '—'}
              </strong>
            </li>
            {row.observedLater !== null && (
              <li className="flex justify-between gap-4">
                <span>{t('fc.legendObservedLater')}</span>
                <strong className="tabular-nums text-respira-text">{n(row.observedLater)}</strong>
              </li>
            )}
          </>
        )}
      </ul>
    </div>
  )
}

export function ForecastChart({ data }: { data: ForecastResult }) {
  const { t } = useI18n()
  const { reduceMotion } = usePreferences()
  const gradientId = useId().replace(/:/g, '')
  const [range, setRange] = useState<RangeId>('all')
  const visibleWeeks = RANGES.find((item) => item.id === range)?.weeks ?? Infinity
  const rows = buildRows(data, visibleWeeks)
  const originKey = `${data.origin.year}-${data.origin.week}`
  const lastKey = rows[rows.length - 1]?.key ?? originKey
  const domain = niceDomain(rows)
  const observedRows = rows.filter((row) => !row.isPrediction && !row.isGap)
  const yearTicks = observedRows.length > YEAR_TICKS_FROM_WEEKS
  // En vistas largas se marca solo el inicio de cada año (la primera semana con dato de cada año).
  const tickKeys = yearTicks
    ? observedRows.filter((row, index) => index === 0 || row.year !== observedRows[index - 1].year).map((row) => row.key)
    : undefined
  const labels = new Map(rows.map((row) => [row.key, yearTicks ? String(row.year) : row.label]))
  const predictionRows = rows.filter((row) => row.isPrediction && row.predicted !== null)
  const hasObserved = rows.some((row) => row.observedLater !== null)

  const legend = [
    { color: COLORS.history, label: t('fc.legendHistory'), kind: 'line' },
    { color: COLORS.predicted, label: t('fc.legendPredicted'), kind: 'dash' },
    { color: COLORS.predicted, label: t('fc.legendBand'), kind: 'band' },
    ...(hasObserved ? [{ color: COLORS.observed, label: t('fc.legendObservedLater'), kind: 'dot' }] : []),
  ]

  return (
    <Card className="p-5 sm:p-6">
      <div>
        <h2 className="font-bold">
          {data.municipality.name} · {t('fc.chartTitle')}
        </h2>
        <p className="mt-1 text-xs leading-5 text-respira-muted">
          {data.origin.is_backtest
            ? t('fc.backtestNote')
            : t('fc.futureNote', { week: data.origin.week, year: data.origin.year })}
        </p>
      </div>
      <ul className="mt-4 flex flex-wrap gap-2 text-xs">
        {legend.map((item) => (
          <li
            key={item.label}
            className="inline-flex items-center gap-2 rounded-full border border-respira-border px-3 py-1.5 font-semibold text-respira-text"
          >
            {item.kind === 'dot' ? (
              <i className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
            ) : item.kind === 'band' ? (
              <i className="h-2.5 w-5 rounded-sm opacity-40" style={{ backgroundColor: item.color }} />
            ) : (
              <i
                className="h-0 w-5 border-t-[3px]"
                style={{ borderColor: item.color, borderStyle: item.kind === 'dash' ? 'dashed' : 'solid' }}
              />
            )}
            {item.label}
          </li>
        ))}
      </ul>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs" role="group" aria-label={t('fc.rangeLabel')}>
        <span className="font-semibold text-respira-muted">{t('fc.rangeLabel')}</span>
        {RANGES.map((item) => {
          const active = item.id === range
          return (
            <button
              key={item.id}
              type="button"
              aria-pressed={active}
              onClick={() => setRange(item.id)}
              className={`rounded-full border px-3 py-1.5 font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-respira-blue-dark ${
                active
                  ? 'border-respira-blue bg-respira-blue text-white'
                  : 'border-respira-border text-respira-text hover:bg-sky-50'
              }`}
            >
              {t(item.label)}
            </button>
          )
        })}
      </div>
      <div className="mt-4 h-[340px] w-full" role="img" aria-label={t('fc.chartAria')}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 28, right: 28, bottom: 8, left: -8 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS.history} stopOpacity={0.28} />
                <stop offset="100%" stopColor={COLORS.history} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--color-respira-border)" vertical={false} />
            <XAxis
              dataKey="key"
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-respira-muted)', fontSize: 12 }}
              tickFormatter={(key: string) => labels.get(key) ?? key}
              ticks={tickKeys}
              interval={yearTicks ? 0 : 'preserveStartEnd'}
              minTickGap={yearTicks ? 4 : 18}
            />
            <YAxis
              allowDecimals={false}
              domain={domain}
              tickLine={false}
              axisLine={false}
              width={48}
              tick={{ fill: 'var(--color-respira-muted)', fontSize: 12 }}
            />
            <Tooltip cursor={{ stroke: 'var(--color-respira-muted)', strokeOpacity: 0.45 }} content={<ForecastTooltip />} />
            <ReferenceArea
              x1={originKey}
              x2={lastKey}
              fill={COLORS.predicted}
              fillOpacity={0.07}
              strokeOpacity={0}
              ifOverflow="visible"
            />
            <ReferenceLine
              x={originKey}
              stroke="var(--color-respira-muted)"
              strokeDasharray="3 3"
              label={{
                value: t('fc.chartFromHere'),
                position: 'top',
                fill: 'var(--color-respira-body)',
                fontSize: 12,
                fontWeight: 600,
              }}
            />
            <Area
              type="monotone"
              dataKey="band"
              stroke="none"
              fill={COLORS.predicted}
              fillOpacity={0.3}
              isAnimationActive={false}
              activeDot={false}
              connectNulls
            />
            <Area
              type="monotone"
              dataKey="cases"
              stroke={COLORS.history}
              strokeWidth={2.6}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{ r: 5, fill: COLORS.history, stroke: COLORS.surface, strokeWidth: 2 }}
              isAnimationActive={!reduceMotion}
              connectNulls={false}
            />
            <Line
              type="linear"
              dataKey="predicted"
              stroke={COLORS.predicted}
              strokeWidth={2.8}
              strokeDasharray="7 5"
              dot={false}
              activeDot={false}
              isAnimationActive={!reduceMotion}
              connectNulls
            />
            {predictionRows.map((row) => (
              <ReferenceDot
                key={row.key}
                x={row.key}
                y={row.predicted ?? 0}
                r={6}
                fill={COLORS.predicted}
                stroke={COLORS.surface}
                strokeWidth={2.5}
                ifOverflow="visible"
                label={{
                  value: Math.round(row.predicted ?? 0),
                  position: 'top',
                  offset: 12,
                  fill: 'var(--color-respira-text)',
                  fontSize: 13,
                  fontWeight: 700,
                }}
              />
            ))}
            <Line
              type="linear"
              dataKey="observedLater"
              stroke="none"
              dot={{ r: 5, fill: COLORS.observed, stroke: COLORS.surface, strokeWidth: 2 }}
              activeDot={false}
              isAnimationActive={false}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
