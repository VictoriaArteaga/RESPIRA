import { FlaskConical } from 'lucide-react'
import { useI18n } from '../../i18n/I18nContext'
import { isDemoData } from '../../services/api'
import { Badge } from './Badge'

/** Indica el origen de los datos mostrados: demostración local o conjunto sintético del servidor. */
export function DataBadge() {
  const { t } = useI18n()
  return (
    <Badge className="border border-sky-200 bg-respira-surface">
      <FlaskConical size={13} className="text-sky-800" aria-hidden="true" />
      {isDemoData ? t('data.demo') : t('data.synthetic')}
    </Badge>
  )
}
