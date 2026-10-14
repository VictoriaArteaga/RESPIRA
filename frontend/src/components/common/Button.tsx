import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

interface ButtonProps extends PropsWithChildren, ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
}

export function Button({ children, className = '', variant = 'primary', ...props }: ButtonProps) {
  const styles =
    variant === 'primary'
      ? 'bg-respira-blue text-white hover:bg-respira-blue-dark'
      : 'border border-respira-border bg-[#FFFEFA] text-respira-text hover:bg-sky-50'

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-respira-blue-dark disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
