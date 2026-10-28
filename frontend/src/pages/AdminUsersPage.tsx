import { RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Badge } from '../components/common/Badge'
import { Button } from '../components/common/Button'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { Loading } from '../components/common/Loading'
import { useAuth } from '../context/AuthContext'
import { listUsers, setUserActive } from '../services/adminService'
import type { AccountStatus, AuthUser, UserRole } from '../types/auth'

const STATUS_LABELS: Record<AccountStatus, string> = {
  pending: 'Pendiente de aprobación',
  active: 'Activa',
  disabled: 'Desactivada',
}

const STATUS_STYLES: Record<AccountStatus, string> = {
  pending: 'bg-amber-100 text-amber-900',
  active: 'bg-emerald-100 text-emerald-900',
  disabled: 'bg-slate-200 text-slate-800',
}

const ROLE_LABELS: Record<UserRole, string> = { admin: 'Administrador', analyst: 'Analista' }

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Ocurrió un error inesperado.'
}

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
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
      setLoadError(errorMessage(reason))
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
      setActionError(errorMessage(reason))
    } finally {
      inFlight.current = false
      setBusyId(null)
    }
  }

  async function confirmDeactivation() {
    const target = confirming
    setConfirming(null)
    if (target) await changeActive(target, false, `Se desactivó la cuenta de ${target.email}.`)
  }

  const busy = busyId !== null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-sky-800">Administración</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Administración de usuarios</h1>
          <p className="mt-2 text-sm text-respira-muted">
            Aprueba solicitudes de cuenta y desactiva o reactiva el acceso. Desactivar no elimina la cuenta.
          </p>
        </div>
        <Button variant="secondary" type="button" onClick={() => void load()} disabled={loading || busy}>
          <RefreshCw size={16} aria-hidden="true" />
          Actualizar
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
          <Loading label="Cargando usuarios..." />
        </Card>
      ) : loadError ? (
        <Card>
          <ErrorState message={loadError} />
        </Card>
      ) : users.length === 0 ? (
        <Card>
          <EmptyState>No hay usuarios registrados.</EmptyState>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-[#F2F5F5] text-xs uppercase tracking-wide text-respira-muted">
                <tr>
                  <th scope="col" className="px-6 py-4 font-semibold">Correo electrónico</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Rol</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Estado</th>
                  <th scope="col" className="px-6 py-4 font-semibold">Creada</th>
                  <th scope="col" className="px-6 py-4 text-right font-semibold">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-respira-border">
                {users.map((item) => {
                  const isSelf = item.id === currentUser?.id
                  const rowBusy = busyId === item.id
                  return (
                    <tr key={item.id} className="hover:bg-sky-50/70">
                      <td className="px-6 py-3.5 font-medium">{item.email}</td>
                      <td className="px-6 py-3.5 text-respira-muted">{ROLE_LABELS[item.role] ?? item.role}</td>
                      <td className="px-6 py-3.5">
                        <Badge className={STATUS_STYLES[item.status]}>{STATUS_LABELS[item.status]}</Badge>
                      </td>
                      <td className="px-6 py-3.5 text-respira-muted">
                        {new Date(item.created_at).toLocaleDateString('es-CO')}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        {isSelf ? (
                          <span className="text-xs text-respira-muted">Tu cuenta</span>
                        ) : item.status === 'pending' ? (
                          <Button
                            type="button"
                            disabled={busy}
                            aria-label={`Aprobar cuenta de ${item.email}`}
                            onClick={() => void changeActive(item, true, `Se aprobó la cuenta de ${item.email}.`)}
                          >
                            {rowBusy ? 'Procesando...' : 'Aprobar'}
                          </Button>
                        ) : item.status === 'active' ? (
                          <Button
                            variant="secondary"
                            type="button"
                            disabled={busy}
                            aria-label={`Desactivar cuenta de ${item.email}`}
                            onClick={() => setConfirming(item)}
                          >
                            {rowBusy ? 'Procesando...' : 'Desactivar'}
                          </Button>
                        ) : (
                          <Button
                            variant="secondary"
                            type="button"
                            disabled={busy}
                            aria-label={`Reactivar cuenta de ${item.email}`}
                            onClick={() => void changeActive(item, true, `Se reactivó la cuenta de ${item.email}.`)}
                          >
                            {rowBusy ? 'Procesando...' : 'Reactivar'}
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
            className="w-full max-w-md rounded-2xl border border-respira-border bg-[#FFFEFA] p-6 shadow-card"
            onKeyDown={(event) => {
              if (event.key === 'Escape') setConfirming(null)
            }}
          >
            <h2 id="deactivate-title" className="text-lg font-bold">¿Desactivar esta cuenta?</h2>
            <p id="deactivate-description" className="mt-2 text-sm text-respira-muted">
              {confirming.email} perderá el acceso de inmediato y su sesión actual se cerrará. La cuenta no se
              elimina y puede reactivarse después.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" type="button" autoFocus onClick={() => setConfirming(null)}>
                Cancelar
              </Button>
              <Button type="button" onClick={() => void confirmDeactivation()}>
                Desactivar cuenta
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
