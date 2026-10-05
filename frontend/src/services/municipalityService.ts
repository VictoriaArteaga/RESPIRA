import type { Municipality } from '../types/municipality'
import { get } from './api'

export function fetchMunicipalities(signal?: AbortSignal): Promise<Municipality[]> {
  return get<Municipality[]>('/api/municipalities', signal)
}

export function fetchMunicipality(id: number, signal?: AbortSignal): Promise<Municipality> {
  return get<Municipality>(`/api/municipalities/${id}`, signal)
}
