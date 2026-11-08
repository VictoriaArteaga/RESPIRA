import { Bell, LogOut, Menu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useI18n } from '../../i18n/I18nContext'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth()
  const { t } = useI18n()

  return (
    <header className="sticky top-0 z-10 flex h-[76px] items-center justify-between border-b border-respira-border bg-respira-chrome/95 px-5 backdrop-blur sm:px-8">
      <div className="flex items-center gap-3">
        <button
          className="rounded-lg p-2 text-respira-muted hover:bg-slate-100 lg:hidden"
          type="button"
          aria-label={t('layout.openMenu')}
          onClick={onMenuClick}
        >
          <Menu size={21} aria-hidden="true" />
        </button>
      </div>

      <div className="flex items-center gap-3 sm:gap-5">
        <span className="hidden text-sm text-respira-muted md:block">{t('header.weekly')}</span>
        {user && (
          <div className="flex items-center gap-2">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-respira-blue text-sm font-bold uppercase text-white"
              aria-hidden="true"
            >
              {user.email.charAt(0)}
            </span>
            <span
              className="hidden max-w-[200px] truncate text-sm font-medium text-respira-text md:block"
              title={user.email}
            >
              {user.email}
            </span>
            <button
              className="rounded-xl p-2.5 text-respira-muted hover:bg-slate-100 lg:hidden"
              type="button"
              aria-label={t('header.logout')}
              title={t('header.logout')}
              onClick={() => void logout()}
            >
              <LogOut size={19} aria-hidden="true" />
            </button>
          </div>
        )}
        <Link
          to="/alerts"
          className="relative rounded-xl p-2.5 text-respira-muted hover:bg-slate-100"
          aria-label={t('header.alerts')}
          title={t('header.alerts')}
        >
          <Bell size={19} aria-hidden="true" />
        </Link>
      </div>
    </header>
  )
}
