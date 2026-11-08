import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useI18n } from '../../i18n/I18nContext'
import type { MunicipalitySummary as MunicipalitySummaryData } from '../../types/municipality'
import { Card } from '../common/Card'

interface MunicipalitySummaryProps {
  municipalities: MunicipalitySummaryData[]
}

export function MunicipalitySummary({ municipalities }: MunicipalitySummaryProps) {
  const { t, locale } = useI18n()
  const entries = municipalities.slice(0, 5)
  const maximumCases = Math.max(...entries.map((municipality) => municipality.cases), 1)

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-respira-border px-5 py-5 sm:px-6">
        <div>
          <h2 className="font-bold text-respira-text">{t('dash.topTitle')}</h2>
          <p className="mt-1 text-xs text-respira-muted">{t('dash.topNote')}</p>
        </div>
        <Link
          to="/municipalities"
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-sky-800 hover:bg-sky-50 hover:text-sky-950"
        >
          {t('common.viewAll')} <ArrowUpRight size={15} aria-hidden="true" />
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="p-6 text-sm text-respira-muted">{t('common.noData')}</p>
      ) : (
        <ol className="divide-y divide-respira-border px-5 sm:px-6">
          {entries.map((municipality, index) => (
            <li key={municipality.id} className="flex items-center gap-4 py-4">
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-extrabold ${
                  index === 0 ? 'bg-respira-blue text-white' : 'bg-sky-100 text-sky-900'
                }`}
              >
                {index + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <Link
                    to={`/municipalities/${municipality.id}`}
                    className="truncate text-sm font-semibold text-respira-text hover:text-respira-link hover:underline"
                  >
                    {municipality.name}
                  </Link>
                  <span className="text-sm font-bold tabular-nums text-respira-text">
                    {municipality.cases.toLocaleString(locale)}
                  </span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-sky-100">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-respira-blue to-[#6F9BB5]"
                    style={{ width: `${(municipality.cases / maximumCases) * 100}%` }}
                  />
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
