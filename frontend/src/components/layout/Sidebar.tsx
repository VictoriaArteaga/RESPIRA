import {
  Activity,
  Bell,
  ChartNoAxesCombined,
  ClipboardList,
  Settings,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navigation = [
  { label: 'Dashboard', path: '/dashboard', icon: ChartNoAxesCombined },
  { label: 'Municipios', path: '/municipalities', icon: Activity },
  { label: 'Casos IRA', path: '/cases', icon: ClipboardList },
  { label: 'Alertas', path: '/alerts', icon: Bell },
  { label: 'Configuración', path: '/settings', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-respira-border bg-white lg:flex">
      <div className="flex h-24 items-center gap-3 border-b border-respira-border px-6">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-respira-yellow text-xl font-black text-respira-text">
          R
        </span>
        <div>
          <p className="text-xl font-extrabold tracking-tight text-respira-text">RESPIRA</p>
          <p className="text-xs text-respira-muted">Sistema de alerta temprana IRA</p>
        </div>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 space-y-1 px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
          Menú principal
        </p>
        {navigation.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-amber-50 text-respira-text'
                  : 'text-respira-muted hover:bg-slate-50 hover:text-respira-text'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={19}
                  strokeWidth={isActive ? 2.4 : 1.8}
                  className={isActive ? 'text-respira-yellow-dark' : ''}
                  aria-hidden="true"
                />
                <span>{label}</span>
                {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-respira-yellow-dark" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="m-4 rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
        <p className="text-xs font-semibold text-amber-950">Versión académica</p>
        <p className="mt-1 text-xs leading-5 text-amber-900/75">
          Información de prueba para el monitoreo de IRA en Nariño.
        </p>
      </div>
    </aside>
  )
}
