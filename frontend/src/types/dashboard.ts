export interface DashboardSummary {
  total_municipalities: number
  total_cases: number
  average_cases: number
  municipality_with_most_cases: string | null
  last_epidemiological_week: number | null
  total_records: number
}
