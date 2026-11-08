import { useI18n } from '../../i18n/I18nContext'

export function Loading({ label }: { label?: string }) {
  const { t } = useI18n()
  return (
    <div className="flex min-h-48 items-center justify-center gap-3 text-sm text-respira-muted" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-respira-border border-t-respira-blue-dark" />
      {label ?? t('common.loading')}
    </div>
  )
}
