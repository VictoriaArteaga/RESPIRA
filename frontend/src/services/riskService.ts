import { get } from './api'
import type { AlertResponse, EndemicChannel, RiskMap } from '../types/risk'

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

export function fetchAlerts(year?: number, week?: number, signal?: AbortSignal): Promise<AlertResponse> {
  const params = new URLSearchParams()
  if (year !== undefined) params.set('year', String(year))
  if (week !== undefined) params.set('week', String(week))
  const query = params.toString()
  return get<AlertResponse>(`/api/alerts${query ? `?${query}` : ''}`, signal)
}

export function fetchMunicipalityRisk(municipalityId: number, year?: number, week?: number, signal?: AbortSignal): Promise<import('../types/risk').MunicipalityRisk> {
  const params = new URLSearchParams()
  if (year !== undefined) params.set('year', String(year))
  if (week !== undefined) params.set('week', String(week))
  const query = params.toString()
  return get<import('../types/risk').MunicipalityRisk>(`/api/municipalities/${municipalityId}/risk${query ? `?${query}` : ''}`, signal)
}
