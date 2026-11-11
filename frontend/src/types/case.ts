export interface IraCase {
  id: number
  municipality_id: number
  epidemiological_week: number
  year: number
  cases: number
  temperature: number | null
  precipitation: number | null
  humidity: number | null
}

export interface CaseSummary {
  municipality_id: number
  total_cases: number
  last_year: number
  last_week: number
}

export interface CaseFilters {
  municipality_id?: number
  year?: number
  epidemiological_week?: number
}
