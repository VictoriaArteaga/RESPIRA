import { AlertCircle, Inbox } from 'lucide-react'
import type { ReactNode } from 'react'
import { useI18n } from '../../i18n/I18nContext'

export function ErrorState({ message }: { message: string }) {
  const { t } = useI18n()
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-6 text-center" role="alert">
      <AlertCircle className="text-rose-600" aria-hidden="true" />
      <p className="max-w-lg text-sm text-respira-muted">{message || t('common.serverError')}</p>
    </div>
  )
}

export function EmptyState({ children }: { children?: ReactNode }) {
  const { t } = useI18n()
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-6 text-center">
      <Inbox className="text-slate-400" aria-hidden="true" />
      <p className="text-sm text-respira-muted">{children ?? t('common.noData')}</p>
    </div>
  )
}
