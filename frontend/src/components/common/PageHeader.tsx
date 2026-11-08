import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow: string
  title: string
  description?: string
  icon?: LucideIcon
  actions?: ReactNode
}

export function PageHeader({ eyebrow, title, description, icon: Icon, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex min-w-0 items-start gap-4">
        {Icon && (
          <span className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-respira-blue text-white shadow-[0_6px_16px_rgba(49,95,125,0.22)] sm:flex">
            <Icon size={22} aria-hidden="true" />
          </span>
        )}
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-sky-800">{eyebrow}</p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-respira-text sm:text-3xl">{title}</h1>
          {description && <p className="mt-2 max-w-3xl text-sm leading-6 text-respira-muted">{description}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </header>
  )
}
