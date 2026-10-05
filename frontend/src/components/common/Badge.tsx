import type { PropsWithChildren } from 'react'

interface BadgeProps extends PropsWithChildren {
  className?: string
}

export function Badge({ children, className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900 ${className}`}>
      {children}
    </span>
  )
}
