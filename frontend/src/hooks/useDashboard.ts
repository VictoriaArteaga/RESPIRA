import { useEffect, useState } from 'react'
import type { DashboardSummary } from '../types/dashboard'
import type { IraCase } from '../types/case'
import type { Municipality } from '../types/municipality'
import { fetchCases } from '../services/caseService'
import { fetchDashboardSummary } from '../services/dashboardService'
import { fetchMunicipalities } from '../services/municipalityService'

export interface DashboardData {
  summary: DashboardSummary
  municipalities: Municipality[]
  cases: IraCase[]
}

interface DashboardState {
  data: DashboardData | null
  loading: boolean
  error: string | null
}

export function useDashboard(): DashboardState {
  const [state, setState] = useState<DashboardState>({
    data: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    const controller = new AbortController()

    async function loadDashboard(): Promise<void> {
      try {
        const [summary, municipalities, cases] = await Promise.all([
          fetchDashboardSummary(controller.signal),
          fetchMunicipalities(controller.signal),
          fetchCases({}, controller.signal),
        ])
        setState({ data: { summary, municipalities, cases }, loading: false, error: null })
      } catch (error) {
        if (controller.signal.aborted) return
        setState({
          data: null,
          loading: false,
          error: error instanceof Error ? error.message : 'No fue posible obtener la información del servidor.',
        })
      }
    }

    void loadDashboard()
    return () => controller.abort()
  }, [])

  return state
}
