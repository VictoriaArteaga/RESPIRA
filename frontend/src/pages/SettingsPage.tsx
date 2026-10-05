import { MonitorCog } from 'lucide-react'
import { Badge } from '../components/common/Badge'
import { Card } from '../components/common/Card'
import { getApiBaseUrl } from '../services/api'

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-amber-800">Preferencias</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Configuración</h1>
        <p className="mt-2 text-sm text-respira-muted">Información de conexión y entorno de la aplicación.</p>
      </div>
      <Card className="max-w-2xl p-6">
        <div className="flex items-start gap-4">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-800">
            <MonitorCog aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold">Conexión con el servicio</h2>
            <p className="mt-1 text-sm text-respira-muted">Dirección configurada para la API RESPIRA.</p>
            <code className="mt-4 block break-all rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {getApiBaseUrl()}
            </code>
            <div className="mt-4">
              <Badge>Datos sintéticos — versión de desarrollo</Badge>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
