import { CircleAlert, ShieldCheck } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import {
  Area,
  Brush,
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
import type { TranslationKey } from '../../i18n/translations'
import { usePreferences } from '../../preferences/PreferencesContext'
import type { EndemicChannel } from '../../types/risk'
import { Card } from '../common/Card'

const COLORS = {
  success: '#27834a',
  expected: '#5E97BE',
  alert: '#d9a400',
  observed: '#e04f4f',
  median: 'var(--color-respira-blue-dark)',
}

type Layer = 'success' | 'expected' | 'alert' | 'median'

interface Row {
  week: number
  observed: number
  median: number | null
  p25: number | null
  p75: number | null
  p90: number | null
  // Series apiladas de las zonas del canal.
  zoneSuccess: number | null
  zoneExpected: number | null
  zoneAlert: number | null
  above: boolean
}

type Status = { label: TranslationKey; className: string }

function statusOf(row: Row): Status {
  if (row.p25 === null || row.p75 === null || row.p90 === null) {
    return { label: 'endemic.statusNoHistory', className: 'text-respira-muted' }
  }
  if (row.observed > row.p90) return { label: 'endemic.statusEpidemic', className: 'text-rose-700' }
  if (row.observed > row.p75) return { label: 'endemic.statusAlert', className: 'text-amber-800' }
  if (row.observed < row.p25) return { label: 'endemic.statusBelow', className: 'text-emerald-800' }
  return { label: 'endemic.statusExpected', className: 'text-sky-800' }
}

function ChannelTooltip({ active, payload }: TooltipProps<number, string>) {
  const { t, locale } = useI18n()
  const row = payload?.[0]?.payload as Row | undefined
  if (!active || !row) return null
  const status = statusOf(row)
  const value = (n: number | null) => (n === null ? '—' : n.toLocaleString(locale))
  const lines: Array<[string, string, string]> = [
    [t('endemic.observed'), value(row.observed), COLORS.observed],
    [t('endemic.p90'), value(row.p90), COLORS.alert],
    [t('endemic.p75'), value(row.p75), COLORS.expected],
    [t('endemic.medianHist'), value(row.median), 'var(--color-respira-blue-dark)'],
    [t('endemic.p25'), value(row.p25), COLORS.success],
  ]

  return (
    <div className="min-w-52 rounded-xl border border-respira-border bg-respira-surface px-3.5 py-3 text-xs shadow-[0_8px_24px_rgba(0,0,0,0.18)]">
      <p className="font-bold text-respira-text">{t('common.weekN', { n: row.week })}</p>
      <p className={`mt-1 font-semibold ${status.className}`}>{t(status.label)}</p>
      <ul className="mt-2 space-y-1 border-t border-respira-border pt-2">
        {lines.map(([label, number, color]) => (
          <li key={label} className="flex items-center justify-between gap-4 text-respira-body">
            <span className="inline-flex items-center gap-2">
              <i className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              {label}
            </span>
            <strong className="tabular-nums text-respira-text">{number}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function EndemicChart({ data }: { data: EndemicChannel }) {
  const { t, locale } = useI18n()
  const { reduceMotion } = usePreferences()
  const [hidden, setHidden] = useState<Set<Layer>>(new Set())

  const rows: Row[] = data.weeks.map((point) => {
    const { lower_limit: p25, upper_limit: p75, upper_alert_limit: p90 } = point
    const hasBands = p25 !== null && p75 !== null && p90 !== null
    return {
      week: point.week,
      observed: point.observed_cases,
      median: point.historical_median,
      p25,
      p75,
      p90,
      zoneSuccess: hasBands ? p25 : null,
      zoneExpected: hasBands ? Math.max(p75 - p25, 0) : null,
      zoneAlert: hasBands ? Math.max(p90 - p75, 0) : null,
      above: hasBands && point.observed_cases > p90,
    }
  })
  const weeksAbove = rows.filter((row) => row.above).length
  const latest = rows[rows.length - 1]
  const peak = rows.reduce<Row | null>(
    (best, row) => (best === null || row.observed > best.observed ? row : best),
    null,
  )

  const toggle = (layer: Layer) =>
    setHidden((current) => {
      const next = new Set(current)
      if (next.has(layer)) next.delete(layer)
      else next.add(layer)
      return next
    })

  const legend: Array<{ layer: Layer | null; label: string; swatch: ReactNode }> = [
    {
      layer: 'success',
      label: t('endemic.zoneSuccess'),
      swatch: <i className="h-3 w-4 rounded-sm" style={{ backgroundColor: COLORS.success, opacity: 0.5 }} />,
    },
    {
      layer: 'expected',
      label: t('endemic.zoneExpected'),
      swatch: <i className="h-3 w-4 rounded-sm" style={{ backgroundColor: COLORS.expected, opacity: 0.6 }} />,
    },
    {
      layer: 'alert',
      label: t('endemic.zoneAlert'),
      swatch: <i className="h-3 w-4 rounded-sm" style={{ backgroundColor: COLORS.alert, opacity: 0.6 }} />,
    },
    {
      layer: 'median',
      label: t('endemic.medianHist'),
      swatch: <i className="h-0 w-5 border-t-2 border-dashed" style={{ borderColor: COLORS.median }} />,
    },
    {
      layer: null,
      label: t('endemic.observed'),
      swatch: <i className="h-1 w-5 rounded-full" style={{ backgroundColor: COLORS.observed }} />,
    },
  ]

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold">
            {data.municipality} · {data.year}
          </h2>
          <p className="mt-1 text-xs text-respira-muted">{t('endemic.chartNote')}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
            weeksAbove > 0 ? 'bg-rose-100 text-rose-900' : 'bg-emerald-100 text-emerald-900'
          }`}
        >
          {weeksAbove > 0 ? <CircleAlert size={14} aria-hidden="true" /> : <ShieldCheck size={14} aria-hidden="true" />}
          {weeksAbove > 0 ? t('endemic.weeksAbove', { n: weeksAbove }) : t('endemic.weeksAboveNone')}
        </span>
      </div>

      <ul className="mt-4 flex flex-wrap gap-2 text-xs">
        {legend.map(({ layer, label, swatch }) => {
          const off = layer !== null && hidden.has(layer)
          return (
            <li key={label}>
              {layer === null ? (
                <span className="inline-flex items-center gap-2 rounded-full border border-respira-border px-3 py-1.5 font-semibold text-respira-text">
                  {swatch}
                  {label}
                </span>
              ) : (
                <button
                  type="button"
                  aria-pressed={!off}
                  title={t('common.toggleSeries', { name: label })}
                  onClick={() => toggle(layer)}
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

      <div className="mt-4 h-[470px] w-full" role="img" aria-label={t('endemic.chartAria')}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 20, right: 20, bottom: 8, left: -8 }}>
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
              domain={[0, 'auto']}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
            />
            <Tooltip
              cursor={{ stroke: 'var(--color-respira-muted)', strokeOpacity: 0.45, strokeWidth: 1 }}
              content={<ChannelTooltip />}
            />
            {!hidden.has('success') && (
              <Area
                type="monotone"
                dataKey="zoneSuccess"
                stackId="zones"
                stroke="none"
                fill={COLORS.success}
                fillOpacity={0.1}
                isAnimationActive={false}
                activeDot={false}
              />
            )}
            {!hidden.has('expected') && (
              <Area
                type="monotone"
                dataKey="zoneExpected"
                stackId="zones"
                stroke="none"
                fill={COLORS.expected}
                fillOpacity={0.26}
                isAnimationActive={false}
                activeDot={false}
              />
            )}
            {!hidden.has('alert') && (
              <Area
                type="monotone"
                dataKey="zoneAlert"
                stackId="zones"
                stroke="none"
                fill={COLORS.alert}
                fillOpacity={0.28}
                isAnimationActive={false}
                activeDot={false}
              />
            )}
            {!hidden.has('median') && (
              <Line
                type="monotone"
                dataKey="median"
                stroke={COLORS.median}
                strokeWidth={1.75}
                strokeDasharray="5 4"
                dot={false}
                activeDot={false}
                isAnimationActive={false}
              />
            )}
            {latest && (
              <ReferenceLine
                x={latest.week}
                stroke="var(--color-respira-muted)"
                strokeDasharray="3 4"
                label={{
                  value: t('endemic.latestWeek', { n: latest.week }),
                  position: 'insideBottomRight',
                  fill: 'var(--color-respira-muted)',
                  fontSize: 11,
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="observed"
              isAnimationActive={!reduceMotion}
              stroke={COLORS.observed}
              strokeWidth={2.75}
              dot={(props: { cx?: number; cy?: number; index?: number; payload?: Row }) =>
                props.payload?.above && props.cx !== undefined && props.cy !== undefined ? (
                  <circle
                    key={`above-${props.index}`}
                    cx={props.cx}
                    cy={props.cy}
                    r={3.5}
                    fill={COLORS.observed}
                    stroke="var(--color-respira-surface)"
                    strokeWidth={2}
                  />
                ) : (
                  <g key={`none-${props.index}`} />
                )
              }
              activeDot={{ r: 5.5, fill: COLORS.observed, stroke: 'var(--color-respira-surface)', strokeWidth: 2 }}
            />
            {peak && (
              <ReferenceDot
                x={peak.week}
                y={peak.observed}
                r={6}
                fill={COLORS.observed}
                stroke="var(--color-respira-surface)"
                strokeWidth={2.5}
                ifOverflow="extendDomain"
                label={{
                  value: t('endemic.maxLabel', { value: peak.observed.toLocaleString(locale) }),
                  position: 'top',
                  fill: 'var(--color-respira-text)',
                  fontSize: 11,
                  fontWeight: 700,
                }}
              />
            )}
            <Brush
              dataKey="week"
              height={30}
              travellerWidth={10}
              stroke="var(--color-respira-blue)"
              fill="var(--color-respira-surface-alt)"
              tickFormatter={(week: number) => `S${week}`}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs text-respira-muted">{t('endemic.zoom')}</p>
      <p className="mt-1 text-xs text-respira-muted">{t('endemic.footnote')}</p>
    </Card>
  )
}
