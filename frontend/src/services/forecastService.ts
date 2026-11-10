import { get } from './api'
import type { ForecastModelId, ForecastModelsSummary, ForecastMunicipality, ForecastResult } from '../types/forecast'

export function fetchForecastMunicipalities(signal?: AbortSignal): Promise<ForecastMunicipality[]> {
  return get<{ municipalities: ForecastMunicipality[] }>('/api/forecast/municipalities', signal).then((r) => r.municipalities)
}

export function fetchForecast(
  divipola: string,
  options: { year?: number; week?: number; model?: ForecastModelId } = {},
  signal?: AbortSignal,
): Promise<ForecastResult> {
  const params = new URLSearchParams()
  if (options.year !== undefined && options.week !== undefined) {
    params.set('year', String(options.year))
    params.set('week', String(options.week))
  }
  if (options.model) params.set('model', options.model)
  const query = params.toString()
  return get<ForecastResult>(`/api/forecast/municipalities/${divipola}${query ? `?${query}` : ''}`, signal)
}

export function fetchForecastModels(signal?: AbortSignal): Promise<ForecastModelsSummary> {
  return get<ForecastModelsSummary>('/api/forecast/models', signal)
}
