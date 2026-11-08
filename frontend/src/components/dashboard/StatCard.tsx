import type { LucideIcon } from 'lucide-react'
import { Card } from '../common/Card'

type Tone = 'blue' | 'green' | 'amber' | 'rose'

const tones: Record<Tone, { icon: string; bar: string }> = {
  blue: { icon: 'bg-sky-100 text-sky-800', bar: 'bg-respira-blue' },
  green: { icon: 'bg-emerald-100 text-emerald-800', bar: 'bg-emerald-600' },
  amber: { icon: 'bg-amber-100 text-amber-800', bar: 'bg-amber-500' },
  rose: { icon: 'bg-rose-100 text-rose-800', bar: 'bg-rose-600' },
}

interface StatCardProps {
  label: string
  value: string
  supportingText: string
  icon: LucideIcon
  tone?: Tone
}

export function StatCard({ label, value, supportingText, icon: Icon, tone = 'blue' }: StatCardProps) {
  return (
    <Card className="relative overflow-hidden p-5 transition-shadow hover:shadow-[0_8px_24px_rgba(36,59,74,0.10)] sm:p-6">
      <span className={`absolute inset-x-0 top-0 h-1 ${tones[tone].bar}`} aria-hidden="true" />
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-respira-muted">{label}</p>
          <p className="mt-3 truncate text-3xl font-extrabold tracking-tight text-respira-text">{value}</p>
          <p className="mt-2 text-xs text-respira-muted">{supportingText}</p>
        </div>
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${tones[tone].icon}`}>
          <Icon size={20} aria-hidden="true" />
        </span>
      </div>
    </Card>
  )
}
