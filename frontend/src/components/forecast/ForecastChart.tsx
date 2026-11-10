import { useId, useState } from 'react'
import {
  Area,
  AreaChart,
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

// Periodos del detalle. La franja de abajo siempre muestra todo el historial; estos botones eligen cuánto se acerca el detalle.
const RANGES = [
  { id: '26w', weeks: 26, label: 'fc.range26w' },
  { id: '1y', weeks: 52, label: 'fc.range1y' },
  { id: '2y', weeks: 104, label: 'fc.range2y' },
  { id: '5y', weeks: 260, label: 'fc.range5y' },
  { id: 'all', weeks: Infinity, label: 'fc.rangeAll' },
] as const
type RangeId = (typeof RANGES)[number]['id']
const DEFAULT_RANGE: RangeId = '26w'

// Con más de esta cantidad de semanas el eje marca un año por etiqueta en vez de "S12", "S13"...
const YEAR_TICKS_FROM_WEEKS = 80
// La zona de estimación se dibuja ampliada: ocupa hasta ~30% del ancho visible (con un tope de 3 veces), para que se lea bien.
const FUTURE_SHARE = 0.3
const FUTURE_MAX_STRETCH = 3

export interface Row {
  key: string
  /** Posición en el eje horizontal: 0, 1, 2… para las semanas con dato; la estimación va más separada (zona ampliada). */
  x: number
  label: string
  year: number
  week: number | null
  cases: number | null
  predicted: number | null
  band: [number, number] | null
  observedLater: number | null
  isPrediction: boolean
}

export function buildRows(data: ForecastResult, visibleWeeks: number): { rows: Row[]; stretch: number } {
  const history = Number.isFinite(visibleWeeks) ? data.history.slice(-visibleWeeks) : data.history
  const rows: Row[] = history.map((point, index) => ({
    key: `${point.year}-${point.week}`,
    x: index,
    label: `S${point.week}`,
    year: point.year,
    week: point.week,
    cases: point.cases,
    predicted: null,
    band: null,
    observedLater: null,
    isPrediction: false,
  }))
  // La estimación parte del último valor observado para que se lea como continuación de la línea.
  const last = rows[rows.length - 1]
  if (last) {
    last.predicted = last.cases
    if (last.cases !== null) last.band = [last.cases, last.cases]
  }

  const sorted = [...data.predictions].sort((a, b) => a.horizon_weeks - b.horizon_weeks)
  const farthest = sorted[sorted.length - 1]?.horizon_weeks ?? 1
  const stretch = Math.min(FUTURE_MAX_STRETCH, Math.max(1, (FUTURE_SHARE * rows.length) / farthest))
  const originX = rows.length - 1
  for (const p of sorted) {
    rows.push({
      key: `${p.target_year}-${p.target_week}`,
      x: originX + p.horizon_weeks * stretch,
      label: `S${p.target_week}`,
      year: p.target_year,
      week: p.target_week,
      cases: null,
      predicted: p.predicted_cases,
      band: [p.interval_low, p.interval_high],
      observedLater: p.observed_cases,
      isPrediction: true,
    })
  }
  return { rows, stretch }
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
  if (!active || !row || row.week === null) return null
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
  const [range, setRange] = useState<RangeId>(DEFAULT_RANGE)
  const visibleWeeks = RANGES.find((item) => item.id === range)?.weeks ?? Infinity
  const { rows, stretch } = buildRows(data, visibleWeeks)

  const observedRows = rows.filter((row) => !row.isPrediction)
  const futureRows = rows.filter((row) => row.isPrediction)
  const originX = Math.max(observedRows.length - 1, 0)
  const lastObserved = observedRows[observedRows.length - 1]
  const maxX = (rows[rows.length - 1]?.x ?? 0) + 0.6
  const futureShare = maxX > 0 ? (maxX - originX) / maxX : 0
  // En vistas muy largas la estimación ocupa muy poco: se quitan las etiquetas (se encimarían) y se avisa cómo verla de cerca.
  const compactFuture = futureShare <= 0.12
  const domain = niceDomain(rows)
  const hasObserved = rows.some((row) => row.observedLater !== null)

  // Marcas del eje horizontal: en vistas largas, un año por marca; en las cortas, una semana de cada pocas, alineadas con la última.
  const yearTicks = observedRows.length > YEAR_TICKS_FROM_WEEKS
  const labels = new Map<number, string>()
  const tickXs: number[] = []
  if (yearTicks) {
    observedRows.forEach((row, index) => {
      if (index === 0 || row.year !== observedRows[index - 1].year) {
        tickXs.push(row.x)
        labels.set(row.x, String(row.year))
      }
    })
  } else {
    const step = Math.max(1, Math.ceil(observedRows.length / 9))
    observedRows.forEach((row, index) => {
      if ((observedRows.length - 1 - index) % step === 0) {
        tickXs.push(row.x)
        labels.set(row.x, row.label)
      }
    })
    for (const row of futureRows) {
      tickXs.push(row.x)
      labels.set(row.x, row.label)
    }
  }

  // Franja con todo el historial: un recuadro marca lo que se ve en el detalle de arriba.
  const total = data.history.length
  const overview = data.history.map((point, index) => ({ x: index, cases: point.cases, year: point.year }))
  const windowStart = Number.isFinite(visibleWeeks) ? Math.max(0, total - visibleWeeks) : 0
  const overviewTicks = overview.filter((p, i) => i === 0 || p.year !== overview[i - 1].year).map((p) => p.x)
  const overviewYear = new Map(overview.map((p) => [p.x, String(p.year)]))

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

      <div className="mt-4 h-[400px] w-full" role="img" aria-label={t('fc.chartAria')}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 40, right: 24, bottom: 8, left: -8 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLORS.history} stopOpacity={0.28} />
                <stop offset="100%" stopColor={COLORS.history} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--color-respira-border)" vertical={false} />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, maxX]}
              ticks={tickXs}
              tickFormatter={(value: number) => labels.get(value) ?? ''}
              interval={0}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-respira-muted)', fontSize: 12 }}
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
              x1={originX}
              x2={maxX}
              fill={COLORS.predicted}
              fillOpacity={0.09}
              strokeOpacity={0}
              ifOverflow="visible"
              label={
                !compactFuture
                  ? {
                      value: t('fc.chartFromHere'),
                      position: 'insideTop',
                      fill: 'var(--color-respira-body)',
                      fontSize: 13,
                      fontWeight: 700,
                    }
                  : undefined
              }
            />
            <ReferenceLine x={originX} stroke="var(--color-respira-muted)" strokeDasharray="3 3" />
            <Area
              type="linear"
              dataKey="band"
              stroke={COLORS.predicted}
              strokeOpacity={0.35}
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
              strokeWidth={3.2}
              strokeDasharray="8 5"
              dot={false}
              activeDot={false}
              isAnimationActive={!reduceMotion}
              connectNulls
            />
            {lastObserved && lastObserved.cases !== null && (
              <ReferenceDot
                x={lastObserved.x}
                y={lastObserved.cases}
                r={6}
                fill={COLORS.history}
                stroke={COLORS.surface}
                strokeWidth={2.5}
                ifOverflow="visible"
              />
            )}
            {futureRows.map((row) => (
              <ReferenceDot
                key={row.key}
                x={row.x}
                y={row.predicted ?? 0}
                r={8}
                fill={COLORS.predicted}
                stroke={COLORS.surface}
                strokeWidth={3}
                ifOverflow="visible"
                label={
                  compactFuture
                    ? undefined
                    : {
                        value: Math.round(row.predicted ?? 0),
                        position: 'top',
                        offset: 14,
                        fill: 'var(--color-respira-text)',
                        fontSize: 16,
                        fontWeight: 800,
                      }
                }
              />
            ))}
            <Line
              type="linear"
              dataKey="observedLater"
              stroke="none"
              dot={{ r: 6, fill: COLORS.observed, stroke: COLORS.surface, strokeWidth: 2 }}
              activeDot={false}
              isAnimationActive={false}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {futureRows.length > 0 && (
        <p className="mt-1 text-xs leading-5 text-respira-muted">
          {compactFuture ? t('fc.zoomHint') : stretch > 1 ? t('fc.stretchNote') : null}
        </p>
      )}

      <div className="mt-5 border-t border-respira-border pt-4">
        <p className="text-xs font-semibold text-respira-muted">{t('fc.overviewLabel')}</p>
        <div className="mt-1 h-[84px] w-full" role="img" aria-label={t('fc.overviewAria')}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={overview} margin={{ top: 6, right: 24, bottom: 0, left: 40 }}>
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, Math.max(total - 1, 1)]}
                ticks={overviewTicks}
                tickFormatter={(value: number) => overviewYear.get(value) ?? ''}
                interval={0}
                tickLine={false}
                axisLine={false}
                tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
              />
              <YAxis hide domain={[0, 'dataMax']} />
              <Area
                type="monotone"
                dataKey="cases"
                stroke={COLORS.history}
                strokeWidth={1.6}
                fill={COLORS.history}
                fillOpacity={0.16}
                dot={false}
                isAnimationActive={false}
                connectNulls={false}
              />
              <ReferenceArea
                x1={windowStart}
                x2={Math.max(total - 1, 1)}
                fill={COLORS.predicted}
                fillOpacity={0.2}
                stroke={COLORS.predicted}
                strokeOpacity={0.9}
                strokeWidth={1.5}
                ifOverflow="visible"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  )
}
