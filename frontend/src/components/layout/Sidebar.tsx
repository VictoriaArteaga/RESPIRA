import {
  Activity,
  Bell,
  ChartNoAxesCombined,
  ClipboardList,
  Map,
  ChartLine,
  Settings,
  Users,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navigation = [
  { label: 'Dashboard', path: '/dashboard', icon: ChartNoAxesCombined },
  { label: 'Municipios', path: '/municipalities', icon: Activity },
  { label: 'Mapa de riesgo', path: '/risk-map', icon: Map },
  { label: 'Canal endémico', path: '/endemic', icon: ChartLine },
  { label: 'Casos IRA', path: '/cases', icon: ClipboardList },
  { label: 'Alertas', path: '/alerts', icon: Bell },
  { label: 'Configuración', path: '/settings', icon: Settings },
]

const adminNavigation = [{ label: 'Administración de usuarios', path: '/admin/users', icon: Users }]

export function Sidebar() {
  const { user } = useAuth()
  // Ocultar el enlace es solo comodidad: el backend y la ruta verifican el rol admin.
  const items = user?.role === 'admin' ? [...navigation, ...adminNavigation] : navigation

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-respira-border bg-[#FBF9F3] lg:flex">
      <div className="flex h-24 items-center gap-3 border-b border-respira-border px-6">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-respira-blue text-xl font-black text-white">
          R
        </span>
        <div>
          <p className="text-xl font-extrabold tracking-tight text-respira-text">RESPIRA</p>
          <p className="text-xs text-respira-muted">Sistema de alerta temprana IRA</p>
        </div>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 space-y-1 px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
          Menú principal
        </p>
        {items.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-sky-100/80 text-respira-text'
                  : 'text-respira-muted hover:bg-sky-50 hover:text-respira-text'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={19}
                  strokeWidth={isActive ? 2.4 : 1.8}
                  className={isActive ? 'text-respira-blue-dark' : ''}
                  aria-hidden="true"
                />
                <span>{label}</span>
                {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-respira-blue-dark" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="m-4 rounded-2xl border border-sky-200 bg-sky-50/80 p-4">
        <p className="text-xs font-semibold text-sky-950">Versión académica</p>
        <p className="mt-1 text-xs leading-5 text-sky-900/75">
          Información de prueba para el monitoreo de IRA en Nariño.
        </p>
      </div>
    </aside>
  )
}
