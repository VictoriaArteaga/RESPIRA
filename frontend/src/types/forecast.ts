export type Trend = 'aumento' | 'estable' | 'disminucion' | 'sin_referencia'
export type ForecastModelId = 'base_global' | 'modelo_a' | 'modelo_b'

export interface ForecastMunicipality {
  divipola_code: string
  name: string
  available_models: ForecastModelId[]
  default_model: ForecastModelId
  has_precipitation: boolean
  has_temperature: boolean
  observed_weeks_pct: number
  last_observed: { year: number; week: number } | null
  median_weekly_cases_2012_2019: number | null
  low_volume: boolean
}

export interface ForecastPrediction {
  horizon_weeks: number
  target_year: number
  target_week: number
  target_week_start: string
  target_week_end: string
  predicted_cases: number
  interval_low: number
  interval_high: number
  reference_cases: number | null
  change_vs_reference_pct: number | null
  trend: Trend
  observed_cases: number | null
  absolute_error: number | null
}

export interface ForecastWarning {
  code: string
  message: string
  params: Record<string, string | number>
}

export interface ForecastVariable {
  key: 'ira_history' | 'precipitation' | 'temperature'
  description: string
  used: boolean
  available_for_municipality: boolean
  available_at_origin: boolean
  historical_coverage_pct: number
}

export interface ForecastEvalBlock {
  n: number
  mae: number
  rmse: number
  wape: number | null
  mae_persistence: number
  improvement_vs_persistence_pct: number
  trend_accuracy: number
  increase_recall: number | null
  interval_coverage_80: number
}

export interface ForecastEvaluation {
  validation_2019: ForecastEvalBlock | null
  test_2022: ForecastEvalBlock | null
  pandemic_2020_2021: ForecastEvalBlock | null
}

export interface ForecastHistoryPoint {
  year: number
  week: number
  week_end: string
  cases: number | null
  status: string
}

export interface ForecastResult {
  municipality: { divipola_code: string; name: string }
  origin: {
    year: number
    week: number
    week_start: string
    week_end: string
    observed_cases: number | null
    is_latest_available: boolean
    is_backtest: boolean
  }
  model: { id: ForecastModelId; label: string; is_default: boolean; available_models: ForecastModelId[]; algorithm: string; trained_through: string }
  predictions: ForecastPrediction[]
  comparison: Array<{ model: ForecastModelId; label: string; predictions: ForecastPrediction[] }>
  reference: { description: string; value: number | null }
  history: ForecastHistoryPoint[]
  variables: ForecastVariable[]
  coverage: { observed_weeks_last_52_pct: number; observed_weeks_total_pct: number; missing_prior_weeks_of_4: number }
  evaluation: Record<string, ForecastEvaluation>
  warnings: ForecastWarning[]
  disclaimer: string
}

export interface ClimateContribution {
  modelo: string
  base: string
  horizonte: number
  periodo: string
  n: number
  mae_con_clima: number
  mae_base: number
  mejora_mae_pct: number
}

export interface ForecastDataExtension {
  ira_last_week: { year: number; week: number }
  ira_public_2023_2025: boolean
  population_through_year: number
  calendar_weeks: Record<string, number>
  calendar_ins_anchors: string[]
  climate_public: Record<string, { municipalities: number; valid_municipality_weeks: number }>
  used_for_training: boolean
  note: string
}

export interface ForecastModelsSummary {
  models: Array<{ id: ForecastModelId; label: string; n_municipalities: number; variables: string[] }>
  climate_contribution: ClimateContribution[]
  trained_at: string
  data_extension?: ForecastDataExtension | null
  disclaimer: string
}
