import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

interface ButtonProps extends PropsWithChildren, ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
}

export function Button({ children, className = '', variant = 'primary', ...props }: ButtonProps) {
  const styles =
    variant === 'primary'
      ? 'bg-respira-yellow text-respira-text hover:bg-respira-yellow-dark'
      : 'border border-respira-border bg-white text-respira-text hover:bg-slate-50'

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-respira-yellow-dark disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
