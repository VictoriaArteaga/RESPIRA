import type { DashboardSummary } from '../types/dashboard'
import { get } from './api'

export function fetchDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
  return get<DashboardSummary>('/api/dashboard', signal)
}
