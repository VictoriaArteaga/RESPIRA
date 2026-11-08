import { useI18n } from '../../i18n/I18nContext'
import type { TranslationKey } from '../../i18n/translations'
import type { RiskLevel } from '../../types/risk'

export const riskMeta: Record<RiskLevel, { label: TranslationKey; color: string; badge: string }> = {
  low: { label: 'risk.low', color: '#27834a', badge: 'bg-emerald-100 text-emerald-900' },
  moderate: { label: 'risk.moderate', color: '#d9a400', badge: 'bg-amber-100 text-amber-950' },
  high: { label: 'risk.high', color: '#c83d3d', badge: 'bg-rose-100 text-rose-900' },
  no_data: { label: 'risk.no_data', color: '#94a3b8', badge: 'bg-slate-100 text-slate-700' },
}

export function RiskBadge({ level, label }: { level: RiskLevel; label?: string }) {
  const { t } = useI18n()
  const meta = riskMeta[level]
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${meta.badge}`}>
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: meta.color }} aria-hidden="true" />
      {label ?? t(meta.label)}
    </span>
  )
}
