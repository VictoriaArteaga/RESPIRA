import type { PropsWithChildren } from 'react'

interface CardProps extends PropsWithChildren {
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <section className={`rounded-2xl border border-respira-border bg-respira-surface/95 shadow-card ${className}`}>
      {children}
    </section>
  )
}
