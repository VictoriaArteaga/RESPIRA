import { SlidersHorizontal } from 'lucide-react'
import type { PropsWithChildren, ReactNode } from 'react'
import { useI18n } from '../../i18n/I18nContext'
import { Card } from './Card'

export function FilterBar({ children, note }: PropsWithChildren<{ note?: ReactNode }>) {
  const { t } = useI18n()
  return (
    <Card className="flex flex-wrap items-end gap-4 p-4 sm:px-5">
      <span className="flex items-center gap-2 pb-2.5 text-sm font-semibold text-respira-text">
        <SlidersHorizontal size={17} className="text-sky-800" aria-hidden="true" />
        {t('common.filters')}
      </span>
      {children}
      {note && <p className="ml-auto pb-2.5 text-xs text-respira-muted">{note}</p>}
    </Card>
  )
}

export function FilterField({ label, children }: PropsWithChildren<{ label: string }>) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold text-respira-text">
      {label}
      {children}
    </label>
  )
}
