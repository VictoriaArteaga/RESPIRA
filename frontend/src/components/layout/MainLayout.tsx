import { X } from 'lucide-react'
import { useState, type PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useI18n } from '../../i18n/I18nContext'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function MainLayout({ children }: PropsWithChildren) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user } = useAuth()
  const { t } = useI18n()

  return (
    <div className="app-shell min-h-screen text-respira-text">
      <Sidebar />
      <div className="min-h-screen lg:pl-64">
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="mx-auto w-full max-w-[1600px] p-5 sm:p-8">{children}</main>
      </div>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-30 lg:hidden">
          <button
            className="absolute inset-0 bg-slate-950/40"
            type="button"
            aria-label={t('layout.closeMenu')}
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative flex h-full w-72 flex-col bg-respira-surface shadow-xl">
            <div className="flex items-center justify-between border-b border-respira-border px-5 py-5">
              <span className="font-extrabold tracking-tight">RESPIRA</span>
              <button
                className="rounded-lg p-2 text-respira-muted hover:bg-slate-100"
                type="button"
                aria-label={t('layout.closeMenu')}
                onClick={() => setMobileMenuOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <nav className="space-y-1 p-4" aria-label={t('layout.navAria')}>
              {[
                [t('nav.dashboard'), '/dashboard'],
                [t('nav.municipalities'), '/municipalities'],
                [t('nav.riskMap'), '/risk-map'],
                [t('nav.endemic'), '/endemic'],
                [t('nav.cases'), '/cases'],
                [t('nav.alerts'), '/alerts'],
                [t('nav.settings'), '/settings'],
                ...(user?.role === 'admin' ? [[t('nav.admin'), '/admin/users']] : []),
              ].map(([label, path]) => (
                <NavLink
                  key={path}
                  to={path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block rounded-xl px-3 py-3 text-sm font-medium ${
                      isActive ? 'bg-sky-100/70 text-respira-text' : 'text-respira-muted hover:bg-sky-50'
                    }`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </div>
  )
}
