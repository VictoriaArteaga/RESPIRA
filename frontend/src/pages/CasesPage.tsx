import { ChevronLeft, ChevronRight, ClipboardList } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Card } from '../components/common/Card'
import { DataBadge } from '../components/common/DataBadge'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { useI18n } from '../i18n/I18nContext'
import { fetchCases } from '../services/caseService'
import { fetchMunicipalities } from '../services/municipalityService'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'

const PAGE_SIZE = 20

export function CasesPage() {
  const { t, locale } = useI18n()
  const [cases, setCases] = useState<IraCase[]>([])
  const [municipalities, setMunicipalities] = useState<Municipality[]>([])
  const [year, setYear] = useState('')
  const [week, setWeek] = useState('')
  const [municipalityId, setMunicipalityId] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([fetchCases({}, controller.signal), fetchMunicipalities(controller.signal)])
      .then(([caseData, municipalityData]) => {
        setCases(caseData)
        setMunicipalities(municipalityData)
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

  const names = useMemo(() => new Map(municipalities.map((item) => [item.id, item.name])), [municipalities])
  const years = useMemo(() => [...new Set(cases.map((record) => record.year))].sort((a, b) => b - a), [cases])
  const weeks = useMemo(
    () =>
      [
        ...new Set(
          cases.filter((record) => !year || record.year === Number(year)).map((record) => record.epidemiological_week),
        ),
      ].sort((a, b) => a - b),
    [cases, year],
  )
  const filteredCases = useMemo(
    () =>
      cases
        .filter(
          (record) =>
            (!year || record.year === Number(year)) &&
            (!week || record.epidemiological_week === Number(week)) &&
            (!municipalityId || record.municipality_id === Number(municipalityId)),
        )
        .sort(
          (a, b) =>
            b.year - a.year || b.epidemiological_week - a.epidemiological_week || a.municipality_id - b.municipality_id,
        ),
    [cases, municipalityId, week, year],
  )

  const pageCount = Math.max(1, Math.ceil(filteredCases.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const rows = filteredCases.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
  const maximumCases = Math.max(...filteredCases.map((record) => record.cases), 1)
  const totalFiltered = filteredCases.reduce((sum, record) => sum + record.cases, 0)

  const change = (setter: (value: string) => void) => (value: string) => {
    setter(value)
    setPage(1)
  }

  const pagerButton =
    'inline-flex items-center gap-1 rounded-lg border border-respira-border bg-respira-surface px-3 py-1.5 font-semibold text-respira-text hover:bg-sky-50 disabled:opacity-50'

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('cases.eyebrow')}
        title={t('cases.title')}
        icon={ClipboardList}
        description={t('cases.description')}
        actions={<DataBadge />}
      />
      <FilterBar>
        <FilterField label={t('common.year')}>
          <select
            className="field-control"
            value={year}
            onChange={(event) => {
              change(setYear)(event.target.value)
              setWeek('')
            }}
          >
            <option value="">{t('common.all')}</option>
            {years.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('common.week')}>
          <select className="field-control" value={week} onChange={(event) => change(setWeek)(event.target.value)}>
            <option value="">{t('common.allF')}</option>
            {weeks.map((value) => (
              <option key={value} value={value}>
                {t('common.weekN', { n: value })}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('common.municipality')}>
          <select
            className="field-control min-w-48"
            value={municipalityId}
            onChange={(event) => change(setMunicipalityId)(event.target.value)}
          >
            <option value="">{t('common.all')}</option>
            {municipalities.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
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
      ) : cases.length === 0 ? (
        <Card>
          <EmptyState />
        </Card>
      ) : filteredCases.length === 0 ? (
        <Card>
          <EmptyState>{t('common.noFilterResults')}</EmptyState>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-respira-border px-5 py-4 text-sm text-respira-muted">
            <p>
              {t('cases.summary', {
                records: filteredCases.length.toLocaleString(locale),
                total: totalFiltered.toLocaleString(locale),
              })}
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-respira-subtle text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('cases.colYear')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('cases.colWeek')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('cases.colMunicipality')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('cases.colCases')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-respira-border">
                {rows.map((record) => (
                  <tr key={record.id} className="transition-colors hover:bg-sky-50/70">
                    <td className="px-6 py-3.5 tabular-nums">{record.year}</td>
                    <td className="px-6 py-3.5">
                      <span className="rounded-full bg-sky-100/80 px-2.5 py-1 text-xs font-semibold text-sky-950">
                        {t('common.weekN', { n: record.epidemiological_week })}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-medium">
                      {names.get(record.municipality_id) ?? record.municipality_id}
                    </td>
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <span className="w-10 font-semibold tabular-nums">{record.cases.toLocaleString(locale)}</span>
                        <div className="h-1.5 w-28 overflow-hidden rounded-full bg-sky-100">
                          <div
                            className="h-full rounded-full bg-respira-blue"
                            style={{ width: `${(record.cases / maximumCases) * 100}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-respira-border px-5 py-3 text-sm">
            <span className="text-respira-muted">{t('cases.page', { page: currentPage, pages: pageCount })}</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className={pagerButton}
                disabled={currentPage === 1}
                onClick={() => setPage(currentPage - 1)}
              >
                <ChevronLeft size={15} aria-hidden="true" /> {t('cases.prev')}
              </button>
              <button
                type="button"
                className={pagerButton}
                disabled={currentPage === pageCount}
                onClick={() => setPage(currentPage + 1)}
              >
                {t('cases.next')} <ChevronRight size={15} aria-hidden="true" />
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
