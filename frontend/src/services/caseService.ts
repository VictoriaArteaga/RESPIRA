import type { CaseFilters, IraCase } from '../types/case'
import { get } from './api'

export function fetchCases(filters: CaseFilters = {}, signal?: AbortSignal): Promise<IraCase[]> {
  const query = new URLSearchParams()
  if (filters.municipality_id !== undefined) {
    query.set('municipality_id', String(filters.municipality_id))
  }
  if (filters.year !== undefined) query.set('year', String(filters.year))
  if (filters.epidemiological_week !== undefined) {
    query.set('epidemiological_week', String(filters.epidemiological_week))
  }
  const search = query.size > 0 ? `?${query.toString()}` : ''
  return get<IraCase[]>(`/api/cases${search}`, signal)
}
