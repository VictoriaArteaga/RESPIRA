export function Loading({ label = 'Obteniendo información...' }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center gap-3 text-sm text-respira-muted" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-respira-border border-t-respira-yellow-dark" />
      {label}
    </div>
  )
}
