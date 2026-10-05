export interface Municipality {
  id: number
  name: string
  department: string
  latitude: number
  longitude: number
}

export interface MunicipalitySummary extends Municipality {
  cases: number
  latestYear: number | null
  latestWeek: number | null
}
