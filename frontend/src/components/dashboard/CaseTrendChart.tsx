import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useI18n } from '../../i18n/I18nContext'
import type { IraCase } from '../../types/case'
import { Card } from '../common/Card'
import { EmptyState } from '../common/Feedback'

interface CaseTrendChartProps {
  cases: IraCase[]
}

export function CaseTrendChart({ cases }: CaseTrendChartProps) {
  const { t, locale } = useI18n()
  const latestYear = Math.max(...cases.map((record) => record.year), 0)
  const weeklyTotals = cases
    .filter((record) => record.year === latestYear)
    .reduce<Record<number, number>>((totals, record) => {
      totals[record.epidemiological_week] = (totals[record.epidemiological_week] ?? 0) + record.cases
      return totals
    }, {})
  const chartData = Object.entries(weeklyTotals)
    .map(([week, totalCases]) => ({ week: Number(week), cases: totalCases }))
    .sort((left, right) => left.week - right.week)
  const peak = chartData.reduce((best, point) => (point.cases > best.cases ? point : best), { week: 0, cases: 0 })

  return (
    <Card className="p-5 sm:p-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-respira-text">{t('dash.trendTitle')}</h2>
          <p className="mt-1 text-xs text-respira-muted">
            {t('dash.trendNote')}
            {latestYear ? ` · ${latestYear}` : ''}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {peak.cases > 0 && (
            <span className="rounded-full bg-sky-100/80 px-3 py-1 text-xs font-semibold text-sky-950">
              {t('dash.trendPeak', { week: peak.week, cases: peak.cases.toLocaleString(locale) })}
            </span>
          )}
          <span className="inline-flex items-center gap-2 text-xs text-respira-muted">
            <span className="h-2.5 w-2.5 rounded-full bg-respira-blue" />
            {t('dash.trendLegend')}
          </span>
        </div>
      </div>
      {chartData.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="h-[290px] w-full" role="img" aria-label={t('dash.trendAria')}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 4 }}>
              <defs>
                <linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-respira-blue)" stopOpacity={0.28} />
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
                tickLine={false}
                axisLine={false}
                tick={{ fill: 'var(--color-respira-muted)', fontSize: 11 }}
              />
              <Tooltip
                cursor={{
                  stroke: 'var(--color-respira-blue)',
                  strokeOpacity: 0.25,
                  strokeWidth: 1,
                }}
                labelFormatter={(week) => t('dash.trendTooltip', { week: String(week) })}
                formatter={(value) => [Number(value).toLocaleString(locale), t('common.cases')]}
                contentStyle={{
                  border: '1px solid var(--color-respira-border)',
                  background: 'var(--color-respira-surface)',
                  color: 'var(--color-respira-text)',
                  borderRadius: '12px',
                  boxShadow: '0 8px 24px rgba(36, 59, 74, 0.10)',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey="cases"
                name="Casos"
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
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}
