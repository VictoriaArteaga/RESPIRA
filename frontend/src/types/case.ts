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

export interface CaseFilters {
  municipality_id?: number
  year?: number
  epidemiological_week?: number
}
