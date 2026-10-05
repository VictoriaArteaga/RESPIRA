export interface IraCase {
  id: number
  municipality_id: number
  epidemiological_week: number
  year: number
  cases: number
  temperature: number
  precipitation: number
  humidity: number
}

export interface CaseFilters {
  municipality_id?: number
  year?: number
  epidemiological_week?: number
}
