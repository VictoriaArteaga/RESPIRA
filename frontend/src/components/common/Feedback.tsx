import { AlertCircle, Inbox } from 'lucide-react'
import type { ReactNode } from 'react'

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-6 text-center" role="alert">
      <AlertCircle className="text-rose-600" aria-hidden="true" />
      <p className="max-w-lg text-sm text-respira-muted">
        {message || 'No fue posible obtener la información del servidor.'}
      </p>
    </div>
  )
}

export function EmptyState({ children = 'No hay datos disponibles.' }: { children?: ReactNode }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 p-6 text-center">
      <Inbox className="text-slate-400" aria-hidden="true" />
      <p className="text-sm text-respira-muted">{children}</p>
    </div>
  )
}
