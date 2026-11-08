import { RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import { listUsers, setUserActive } from '../services/adminService'
import type { AccountStatus, AuthUser, UserRole } from '../types/auth'

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

const ROLE_LABELS: Record<UserRole, TranslationKey> = { admin: 'admin.roleAdmin', analyst: 'admin.roleAnalyst' }

function errorMessage(reason: unknown, fallback: string): string {
  return reason instanceof Error ? reason.message : fallback
}

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const { t, locale } = useI18n()
  const [users, setUsers] = useState<AuthUser[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [confirming, setConfirming] = useState<AuthUser | null>(null)
  // Evita peticiones duplicadas por doble clic antes de que React pinte el estado deshabilitado.
  const inFlight = useRef(false)

  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      setUsers(await listUsers())
    } catch (reason) {
      setLoadError(errorMessage(reason, t('common.unexpected')))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function changeActive(target: AuthUser, isActive: boolean, successMessage: string) {
    if (inFlight.current) return
    inFlight.current = true
    setBusyId(target.id)
    setActionError(null)
    setNotice(null)
    try {
      await setUserActive(target.id, isActive)
      setNotice(successMessage)
      await load()
    } catch (reason) {
      setActionError(errorMessage(reason, t('common.unexpected')))
    } finally {
      inFlight.current = false
      setBusyId(null)
    }
  }

  async function confirmDeactivation() {
    const target = confirming
    setConfirming(null)
    if (target) await changeActive(target, false, t('admin.deactivated', { email: target.email }))
  }

  const busy = busyId !== null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-sky-800">{t('admin.eyebrow')}</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">{t('admin.title')}</h1>
          <p className="mt-2 text-sm text-respira-muted">{t('admin.description')}</p>
        </div>
        <Button variant="secondary" type="button" onClick={() => void load()} disabled={loading || busy}>
          <RefreshCw size={16} aria-hidden="true" />
          {t('common.refresh')}
        </Button>
      </div>

      {notice && (
        <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900" role="status">
          {notice}
        </p>
      )}
      {actionError && (
        <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800" role="alert">
          {actionError}
        </p>
      )}

      {loading && users.length === 0 ? (
        <Card>
          <Loading label={t('admin.loadingUsers')} />
        </Card>
      ) : loadError ? (
        <Card>
          <ErrorState message={loadError} />
        </Card>
      ) : users.length === 0 ? (
        <Card>
          <EmptyState>{t('admin.empty')}</EmptyState>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-respira-subtle text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('admin.colEmail')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('admin.colRole')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('admin.colStatus')}
                  </th>
                  <th scope="col" className="px-6 py-4 font-semibold">
                    {t('admin.colCreated')}
                  </th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">
                    {t('admin.colActions')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-respira-border">
                {users.map((item) => {
                  const isSelf = item.id === currentUser?.id
                  const rowBusy = busyId === item.id
                  return (
                    <tr key={item.id} className="hover:bg-sky-50/70">
                      <td className="px-6 py-3.5 font-medium">{item.email}</td>
                      <td className="px-6 py-3.5 text-respira-muted">
                        {ROLE_LABELS[item.role] ? t(ROLE_LABELS[item.role]) : item.role}
                      </td>
                      <td className="px-6 py-3.5">
                        <Badge className={STATUS_STYLES[item.status]}>{t(STATUS_LABELS[item.status])}</Badge>
                      </td>
                      <td className="px-6 py-3.5 text-respira-muted">
                        {new Date(item.created_at).toLocaleDateString(locale)}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        {isSelf ? (
                          <span className="text-xs text-respira-muted">{t('admin.yourAccount')}</span>
                        ) : item.status === 'pending' ? (
                          <Button
                            type="button"
                            disabled={busy}
                            aria-label={t('admin.approveLabel', { email: item.email })}
                            onClick={() => void changeActive(item, true, t('admin.approved', { email: item.email }))}
                          >
                            {rowBusy ? t('common.processing') : t('admin.approve')}
                          </Button>
                        ) : item.status === 'active' ? (
                          <Button
                            variant="secondary"
                            type="button"
                            disabled={busy}
                            aria-label={t('admin.deactivateLabel', { email: item.email })}
                            onClick={() => setConfirming(item)}
                          >
                            {rowBusy ? t('common.processing') : t('admin.deactivate')}
                          </Button>
                        ) : (
                          <Button
                            variant="secondary"
                            type="button"
                            disabled={busy}
                            aria-label={t('admin.reactivateLabel', { email: item.email })}
                            onClick={() => void changeActive(item, true, t('admin.reactivated', { email: item.email }))}
                          >
                            {rowBusy ? t('common.processing') : t('admin.reactivate')}
                          </Button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {confirming && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-5">
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="deactivate-title"
            aria-describedby="deactivate-description"
            className="w-full max-w-md rounded-2xl border border-respira-border bg-respira-surface p-6 shadow-card"
            onKeyDown={(event) => {
              if (event.key === 'Escape') setConfirming(null)
            }}
          >
            <h2 id="deactivate-title" className="text-lg font-bold">
              {t('admin.confirmTitle')}
            </h2>
            <p id="deactivate-description" className="mt-2 text-sm text-respira-muted">
              {t('admin.confirmText', { email: confirming.email })}
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" type="button" autoFocus onClick={() => setConfirming(null)}>
                {t('common.cancel')}
              </Button>
              <Button type="button" onClick={() => void confirmDeactivation()}>
                {t('admin.confirmButton')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
