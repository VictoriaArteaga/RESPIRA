import { CalendarDays, CircleUser, Fingerprint, KeyRound, Mail, ShieldCheck, ToggleRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Card } from '../components/common/Card'
import { EmptyState } from '../components/common/Feedback'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import type { AccountStatus, UserRole } from '../types/auth'

const ROLE_LABELS: Record<UserRole, TranslationKey> = { admin: 'admin.roleAdmin', analyst: 'admin.roleAnalyst' }
const STATUS_LABELS: Record<AccountStatus, TranslationKey> = {
  pending: 'admin.statusPending',
  active: 'admin.statusActive',
  disabled: 'admin.statusDisabled',
}
const STATUS_STYLES: Record<AccountStatus, string> = {
  pending: 'bg-amber-100 text-amber-900',
  active: 'bg-emerald-100 text-emerald-900',
  disabled: 'bg-slate-200 text-slate-800',
}

function Detail({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-respira-border bg-respira-surface-alt p-4">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-sky-100 text-sky-800">
        <Icon size={19} aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <dt className="text-xs text-respira-muted">{label}</dt>
        <dd className="mt-1 break-words text-sm font-semibold text-respira-text">{children}</dd>
      </div>
    </div>
  )
}

export function ProfilePage() {
  const { t, locale } = useI18n()
  const { user } = useAuth()

  if (!user) {
    return (
      <Card>
        <EmptyState>{t('profile.unavailable')}</EmptyState>
      </Card>
    )
  }

  const created = new Date(user.created_at)
  const createdText = Number.isNaN(created.getTime())
    ? '—'
    : created.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
  const isAdmin = user.role === 'admin'
  const permissions = [t('profile.permView'), t('profile.permPrefs'), ...(isAdmin ? [t('profile.permAdmin')] : [])]

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('profile.eyebrow')}
        title={t('profile.title')}
        icon={CircleUser}
        description={t('profile.description')}
      />

      <Card className="relative overflow-hidden p-6 sm:p-8">
        <span className="absolute inset-x-0 top-0 h-1 bg-respira-blue" aria-hidden="true" />
        <div className="flex flex-wrap items-center gap-5">
          <span
            className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-respira-blue text-3xl font-extrabold uppercase text-white shadow-[0_6px_16px_rgba(49,95,125,0.25)]"
            aria-hidden="true"
          >
            {user.email.charAt(0)}
          </span>
          <div className="min-w-0">
            <p className="break-words text-xl font-extrabold tracking-tight">{user.email}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full bg-sky-100/80 px-3 py-1 text-xs font-semibold text-sky-950">
                <ShieldCheck size={13} aria-hidden="true" />
                {t(ROLE_LABELS[user.role])}
              </span>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[user.status]}`}>
                {t(STATUS_LABELS[user.status])}
              </span>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Card className="p-5 sm:p-6">
          <h2 className="font-bold">{t('profile.account')}</h2>
          <dl className="mt-5 grid gap-4 sm:grid-cols-2">
            <Detail icon={Mail} label={t('profile.email')}>
              {user.email}
            </Detail>
            <Detail icon={Fingerprint} label={t('profile.id')}>
              #{user.id}
            </Detail>
            <Detail icon={KeyRound} label={t('profile.role')}>
              {t(ROLE_LABELS[user.role])}
            </Detail>
            <Detail icon={ShieldCheck} label={t('profile.status')}>
              {t(STATUS_LABELS[user.status])}
            </Detail>
            <Detail icon={ToggleRight} label={t('profile.active')}>
              {user.is_active ? t('profile.yes') : t('profile.no')}
            </Detail>
            <Detail icon={CalendarDays} label={t('profile.created')}>
              {createdText}
            </Detail>
          </dl>
        </Card>

        <Card className="p-5 sm:p-6">
          <h2 className="font-bold">{t('profile.access')}</h2>
          <p className="mt-1 text-xs text-respira-muted">{t('profile.accessNote')}</p>
          <ul className="mt-5 space-y-3 text-sm">
            {permissions.map((permission) => (
              <li key={permission} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-800">
                  <ShieldCheck size={12} aria-hidden="true" />
                </span>
                <span className="leading-6 text-respira-body">{permission}</span>
              </li>
            ))}
          </ul>
          {!isAdmin && <p className="mt-4 text-xs leading-5 text-respira-muted">{t('profile.noAdmin')}</p>}
        </Card>
      </div>
    </div>
  )
}
