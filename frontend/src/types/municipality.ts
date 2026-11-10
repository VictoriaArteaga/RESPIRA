export interface Municipality {
  id: number
  name: string
  department: string
  latitude: number
  longitude: number
  /** Solo en modo demostración: copia de un municipio real con datos de prueba (no es un municipio adicional). */
  simulated?: boolean
}

export interface MunicipalitySummary extends Municipality {
  cases: number
  latestYear: number | null
  latestWeek: number | null
}
