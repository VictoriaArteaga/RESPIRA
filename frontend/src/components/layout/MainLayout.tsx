import { X } from 'lucide-react'
import { useState, type PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function MainLayout({ children }: PropsWithChildren) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-respira-background text-respira-text">
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
            aria-label="Cerrar menú"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative flex h-full w-72 flex-col bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-respira-border px-5 py-5">
              <span className="font-extrabold tracking-tight">RESPIRA</span>
              <button
                className="rounded-lg p-2 text-respira-muted hover:bg-slate-100"
                type="button"
                aria-label="Cerrar menú"
                onClick={() => setMobileMenuOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <nav className="space-y-1 p-4" aria-label="Navegación principal">
              {[
                ['Dashboard', '/dashboard'],
                ['Municipios', '/municipalities'],
                ['Casos IRA', '/cases'],
                ['Alertas', '/alerts'],
                ['Configuración', '/settings'],
              ].map(([label, path]) => (
                <NavLink
                  key={path}
                  to={path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `block rounded-xl px-3 py-3 text-sm font-medium ${
                      isActive ? 'bg-amber-50 text-respira-text' : 'text-respira-muted hover:bg-slate-50'
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
