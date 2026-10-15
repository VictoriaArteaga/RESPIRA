export type RiskLevel = 'low' | 'moderate' | 'high' | 'no_data'

export interface MunicipalityRisk {
  municipality_id: number
  municipality: string
  department: string
  latitude: number
  longitude: number
  year: number | null
  week: number | null
  current_cases: number | null
  historical_average: number | null
  variation_percent: number | null
  risk_level: RiskLevel
}

export interface RiskMap {
  year: number | null
  week: number | null
  available_years: number[]
  municipalities: MunicipalityRisk[]
}

export interface EndemicPoint {
  week: number
  observed_cases: number
  historical_median: number | null
  lower_limit: number | null
  upper_limit: number | null
  upper_alert_limit: number | null
}

export interface EndemicChannel {
  municipality_id: number
  municipality: string
  year: number | null
  available_years: number[]
  statistics: {
    total_cases: number
    average: number
    median: number
    minimum: number
    maximum: number
    risk_level: RiskLevel
    latest_week: number | null
  } | null
  weeks: EndemicPoint[]
}

export interface EpidemiologicalAlert {
  municipality_id: number
  municipality: string
  year: number
  week: number
  observed_cases: number
  historical_average: number
  variation_percent: number
  risk_level: 'moderate' | 'high'
  reason: string
}

export interface AlertResponse {
  year: number | null
  week: number | null
  available_years: number[]
  alerts: EpidemiologicalAlert[]
}
