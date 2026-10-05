import { Bell } from 'lucide-react'
import { Card } from '../components/common/Card'

export function AlertsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-amber-800">Seguimiento</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Alertas</h1>
      </div>
      <Card className="flex min-h-64 flex-col items-center justify-center p-8 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-800">
          <Bell aria-hidden="true" />
        </span>
        <h2 className="mt-4 font-semibold">Módulo en preparación</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-respira-muted">
          El módulo de alertas será implementado en una etapa posterior.
        </p>
      </Card>
    </div>
  )
}
