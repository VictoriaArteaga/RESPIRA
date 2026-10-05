import { Bell, Menu } from 'lucide-react'
import { Badge } from '../common/Badge'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-[76px] items-center justify-between border-b border-respira-border bg-white/95 px-5 backdrop-blur sm:px-8">
      <div className="flex items-center gap-3">
        <button
          className="rounded-lg p-2 text-respira-muted hover:bg-slate-100 lg:hidden"
          type="button"
          aria-label="Abrir menú de navegación"
          onClick={onMenuClick}
        >
          <Menu size={21} aria-hidden="true" />
        </button>
        <div>
          <p className="text-sm font-semibold text-respira-text">RESPIRA</p>
          <p className="hidden text-xs text-respira-muted sm:block">Monitoreo epidemiológico · Nariño</p>
        </div>
      </div>

      <div className="flex items-center gap-3 sm:gap-5">
        <span className="hidden text-sm text-respira-muted md:block">Seguimiento semanal</span>
        <Badge>
          <span className="h-1.5 w-1.5 rounded-full bg-amber-600" />
          Datos de prueba
        </Badge>
        <button
          type="button"
          className="relative rounded-xl p-2.5 text-respira-muted hover:bg-slate-100"
          aria-label="Notificaciones (próximamente)"
          title="Notificaciones disponibles próximamente"
          disabled
        >
          <Bell size={19} aria-hidden="true" />
        </button>
      </div>
    </header>
  )
}
