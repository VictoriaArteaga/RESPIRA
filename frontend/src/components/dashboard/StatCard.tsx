import type { LucideIcon } from 'lucide-react'
import { Card } from '../common/Card'

interface StatCardProps {
  label: string
  value: string
  supportingText: string
  icon: LucideIcon
}

export function StatCard({ label, value, supportingText, icon: Icon }: StatCardProps) {
  return (
    <Card className="p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-respira-muted">{label}</p>
          <p className="mt-3 truncate text-2xl font-bold tracking-tight text-respira-text">{value}</p>
          <p className="mt-2 text-xs text-respira-muted">{supportingText}</p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-800">
          <Icon size={20} aria-hidden="true" />
        </span>
      </div>
    </Card>
  )
}
