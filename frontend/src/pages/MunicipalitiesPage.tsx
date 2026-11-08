import { ChevronRight, MapPinned, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { DataBadge } from '../components/common/DataBadge'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { useI18n } from '../i18n/I18nContext'
import { fetchCases } from '../services/caseService'
import { fetchMunicipalities } from '../services/municipalityService'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'

export function MunicipalitiesPage() {
  const { t, locale } = useI18n()
  const [municipalities, setMunicipalities] = useState<Municipality[]>([])
  const [cases, setCases] = useState<IraCase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([fetchMunicipalities(controller.signal), fetchCases({}, controller.signal)])
      .then(([municipalityData, caseData]) => {
        setMunicipalities(municipalityData)
        setCases(caseData)
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : t('common.serverError'))
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const totals = useMemo(() => {
    const byMunicipality = new Map<number, { cases: number; year: number; week: number }>()
    for (const record of cases) {
      const current = byMunicipality.get(record.municipality_id) ?? { cases: 0, year: 0, week: 0 }
      current.cases += record.cases
      if (record.year > current.year || (record.year === current.year && record.epidemiological_week > current.week)) {
        current.year = record.year
        current.week = record.epidemiological_week
      }
      byMunicipality.set(record.municipality_id, current)
    }
    return byMunicipality
  }, [cases])

  const maximumCases = Math.max(...[...totals.values()].map((item) => item.cases), 1)
  const visible = municipalities.filter((municipality) =>
    municipality.name.toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('mun.eyebrow')}
        title={t('mun.title')}
        icon={MapPinned}
        description={t('mun.description')}
        actions={<DataBadge />}
      />
      {loading ? (
        <Card>
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error} />
        </Card>
      ) : municipalities.length === 0 ? (
        <Card>
          <EmptyState />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-respira-border px-5 py-4">
            <p className="text-sm text-respira-muted">
              {t('mun.count', { shown: visible.length, total: municipalities.length })}
            </p>
            <label className="relative block w-full sm:w-72">
              <span className="sr-only">{t('mun.search')}</span>
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-respira-muted"
                aria-hidden="true"
              />
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={t('mun.search')}
                className="field-control w-full pl-10"
              />
            </label>
          </div>
          {visible.length === 0 ? (
            <EmptyState>{t('mun.noMatch')}</EmptyState>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-respira-subtle text-xs uppercase tracking-wide text-respira-muted">
                  <tr>
                    <th scope="col" className="px-6 py-4 font-semibold">
                      {t('mun.colName')}
                    </th>
                    <th scope="col" className="px-6 py-4 font-semibold">
                      {t('mun.colCases')}
                    </th>
                    <th scope="col" className="px-6 py-4 text-right font-semibold">
                      {t('mun.colLastWeek')}
                    </th>
                    <th scope="col" className="px-6 py-4 text-right font-semibold">
                      {t('mun.colDetail')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-respira-border">
                  {visible.map((municipality) => {
                    const summary = totals.get(municipality.id)
                    const total = summary?.cases ?? 0
                    return (
                      <tr key={municipality.id} className="transition-colors hover:bg-sky-50/70">
                        <th scope="row" className="px-6 py-4 font-semibold text-respira-text">
                          <span className="flex items-center gap-3">
                            <span
                              className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-100 text-sm font-extrabold text-sky-900"
                              aria-hidden="true"
                            >
                              {municipality.name.charAt(0)}
                            </span>
                            <span>
                              {municipality.name}
                              <span className="block text-xs font-normal text-respira-muted">
                                {municipality.department}
                              </span>
                            </span>
                          </span>
                        </th>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <span className="w-16 font-semibold tabular-nums">{total.toLocaleString(locale)}</span>
                            <div className="h-2 w-32 overflow-hidden rounded-full bg-sky-100">
                              <div
                                className="h-full rounded-full bg-gradient-to-r from-respira-blue to-[#6F9BB5]"
                                style={{ width: `${(total / maximumCases) * 100}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right text-respira-muted">
                          {summary?.year ? `${summary.year} · S${summary.week}` : t('common.noRecords')}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link
                            to={`/municipalities/${municipality.id}`}
                            className="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 font-semibold text-sky-800 hover:bg-sky-100"
                          >
                            {t('common.viewDetail')} <ChevronRight size={15} aria-hidden="true" />
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
