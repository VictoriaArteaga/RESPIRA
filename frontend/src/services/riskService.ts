import { get } from './api'
import type { EndemicChannel, RiskMap } from '../types/risk'

export function fetchRiskMap(year?: number, week?: number, signal?: AbortSignal): Promise<RiskMap> {
  const params = new URLSearchParams()
  if (year !== undefined) params.set('year', String(year))
  if (week !== undefined) params.set('week', String(week))
  const query = params.toString()
  return get<RiskMap>(`/api/risk-map${query ? `?${query}` : ''}`, signal)
}

export function fetchEndemicChannel(municipalityId: number, year: number | undefined, signal?: AbortSignal): Promise<EndemicChannel> {
  const query = year === undefined ? '' : `?year=${year}`
  return get<EndemicChannel>(`/api/municipalities/${municipalityId}/endemic-channel${query}`, signal)
}
