import { CalendarDays, Database, MapPin, TrendingUp } from 'lucide-react'
import { useI18n } from '../../i18n/I18nContext'
import type { DashboardSummary } from '../../types/dashboard'
import { Card } from '../common/Card'

interface RecentDataProps {
  summary: DashboardSummary
  period: string | null
}

export function RecentData({ summary, period }: RecentDataProps) {
  const { t, locale } = useI18n()
  const items = [
    {
      label: t('dash.lastWeekAvail'),
      value: summary.last_epidemiological_week
        ? t('common.weekN', { n: summary.last_epidemiological_week })
        : t('common.noRecords'),
      icon: CalendarDays,
    },
    { label: t('dash.recordsAvail'), value: summary.total_records.toLocaleString(locale), icon: Database },
    {
      label: t('dash.topMunicipality'),
      value: summary.municipality_with_most_cases ?? t('common.noRecords'),
      icon: MapPin,
    },
    { label: t('dash.dataPeriod'), value: period ?? t('common.noRecords'), icon: TrendingUp },
  ]

  return (
    <Card className="p-5 sm:p-6">
      <div className="mb-5">
        <h2 className="font-bold text-respira-text">{t('dash.summaryTitle')}</h2>
        <p className="mt-1 text-xs text-respira-muted">{t('dash.summaryNote')}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {items.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="flex items-start gap-3 rounded-xl border border-respira-border bg-respira-surface-alt p-4"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-sky-100 text-sky-800">
              <Icon size={18} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <p className="text-xs text-respira-muted">{label}</p>
              <p className="mt-1 truncate text-sm font-semibold text-respira-text">{value}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
