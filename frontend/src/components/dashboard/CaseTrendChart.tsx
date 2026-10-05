import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { IraCase } from '../../types/case'
import { Card } from '../common/Card'
import { EmptyState } from '../common/Feedback'

interface CaseTrendChartProps {
  cases: IraCase[]
}

export function CaseTrendChart({ cases }: CaseTrendChartProps) {
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

  return (
    <Card className="p-5 sm:p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-respira-text">Tendencia de casos IRA</h2>
          <p className="mt-1 text-xs text-respira-muted">
            Casos históricos agregados por semana{latestYear ? ` · ${latestYear}` : ''}
          </p>
        </div>
        <span className="inline-flex items-center gap-2 text-xs text-respira-muted">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
          Casos registrados
        </span>
      </div>
      {chartData.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="h-[280px] w-full" role="img" aria-label="Gráfica de casos IRA por semana epidemiológica">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, left: -16, bottom: 4 }}>
              <CartesianGrid stroke="#E2E8F0" strokeDasharray="4 4" vertical={false} />
              <XAxis
                dataKey="week"
                tickLine={false}
                axisLine={false}
                tick={{ fill: '#64748B', fontSize: 11 }}
                tickFormatter={(week: number) => `S${week}`}
                minTickGap={22}
              />
              <YAxis
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
                tick={{ fill: '#64748B', fontSize: 11 }}
              />
              <Tooltip
                labelFormatter={(week) => `Semana epidemiológica ${week}`}
                formatter={(value) => [Number(value).toLocaleString('es-CO'), 'Casos']}
                contentStyle={{
                  border: '1px solid #E2E8F0',
                  borderRadius: '12px',
                  boxShadow: '0 8px 24px rgba(15, 23, 42, 0.08)',
                  fontSize: '12px',
                }}
              />
              <Line
                type="monotone"
                dataKey="cases"
                name="Casos"
                stroke="#D9A400"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5, fill: '#D9A400', stroke: '#FFFFFF', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}
