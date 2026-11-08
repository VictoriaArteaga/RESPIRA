import {
  Activity,
  Bell,
  ChartNoAxesCombined,
  ClipboardList,
  LogOut,
  Map,
  ChartLine,
  CircleUser,
  Settings,
  Users,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useI18n } from '../../i18n/I18nContext'
import type { TranslationKey } from '../../i18n/translations'

const navigation: Array<{ labelKey: TranslationKey; path: string; icon: typeof Activity }> = [
  { labelKey: 'nav.dashboard', path: '/dashboard', icon: ChartNoAxesCombined },
  { labelKey: 'nav.municipalities', path: '/municipalities', icon: Activity },
  { labelKey: 'nav.riskMap', path: '/risk-map', icon: Map },
  { labelKey: 'nav.endemic', path: '/endemic', icon: ChartLine },
  { labelKey: 'nav.cases', path: '/cases', icon: ClipboardList },
  { labelKey: 'nav.alerts', path: '/alerts', icon: Bell },
  { labelKey: 'nav.profile', path: '/profile', icon: CircleUser },
  { labelKey: 'nav.settings', path: '/settings', icon: Settings },
]

const adminNavigation: typeof navigation = [{ labelKey: 'nav.admin', path: '/admin/users', icon: Users }]

export function Sidebar() {
  const { user, logout } = useAuth()
  const { t } = useI18n()
  // Ocultar el enlace es solo comodidad: el backend y la ruta verifican el rol admin.
  const items = user?.role === 'admin' ? [...navigation, ...adminNavigation] : navigation

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col bg-respira-sidebar text-white lg:flex">
      <div className="flex h-[76px] flex-none items-center gap-3 border-b border-respira-border bg-respira-chrome px-6">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-respira-blue text-xl font-black text-white">
          R
        </span>
        <div>
          <p className="text-xl font-extrabold tracking-tight text-respira-text">RESPIRA</p>
          <p className="text-xs text-respira-muted">{t('layout.tagline')}</p>
        </div>
      </div>

      <nav aria-label={t('layout.navAria')} className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-white/70">
          {t('layout.mainMenu')}
        </p>
        {items.map(({ labelKey, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-white transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-white ${
                isActive ? 'bg-white/20 font-semibold' : 'text-white/85 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={19} strokeWidth={isActive ? 2.4 : 1.8} aria-hidden="true" />
                <span>{t(labelKey)}</span>
                {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-white" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="flex-none border-t border-white/15 p-4">
        <button
          type="button"
          onClick={() => void logout()}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-white bg-white px-4 py-3 text-sm font-semibold text-respira-sidebar transition-colors hover:bg-white/90 active:bg-respira-sidebar active:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          <LogOut size={18} aria-hidden="true" />
          {t('header.logout')}
        </button>
      </div>
    </aside>
  )
}
