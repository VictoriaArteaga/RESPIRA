import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as forecastService from '../services/forecastService'
import type { ForecastEvalBlock, ForecastModelsSummary, ForecastMunicipality, ForecastResult } from '../types/forecast'
import { ForecastPage } from './ForecastPage'

vi.mock('../services/forecastService')
// La gráfica depende de medidas del navegador; aquí se verifica el contenido de la página, no el dibujo.
vi.mock('../components/forecast/ForecastChart', () => ({ ForecastChart: () => <div>gráfica</div> }))

const block: ForecastEvalBlock = {
  n: 100, mae: 4.2, rmse: 11.5, wape: 0.28, mae_persistence: 5, improvement_vs_persistence_pct: 15,
  trend_accuracy: 0.57, increase_recall: 0.07, interval_coverage_80: 0.82,
}

const municipalities: ForecastMunicipality[] = [
  {
    divipola_code: '52001', name: 'PASTO', available_models: ['base_global', 'modelo_a', 'modelo_b'], default_model: 'base_global',
    has_precipitation: true, has_temperature: true, observed_weeks_pct: 99.7, last_observed: { year: 2022, week: 52 },
    median_weekly_cases_2012_2019: 300, low_volume: false,
  },
]

const result: ForecastResult = {
  municipality: { divipola_code: '52001', name: 'PASTO' },
  origin: { year: 2022, week: 52, week_start: '2022-12-25', week_end: '2022-12-31', observed_cases: 178, is_latest_available: true, is_backtest: false },
  model: { id: 'base_global', label: 'Base', is_default: true, available_models: ['base_global', 'modelo_a', 'modelo_b'], algorithm: 'x', trained_through: '2019' },
  predictions: [
    { horizon_weeks: 2, target_year: 2023, target_week: 2, target_week_start: '2023-01-08', target_week_end: '2023-01-14', predicted_cases: 195.9, interval_low: 173.6, interval_high: 219.5, reference_cases: 226.2, change_vs_reference_pct: -13.4, trend: 'estable', observed_cases: null, absolute_error: null },
    { horizon_weeks: 3, target_year: 2023, target_week: 3, target_week_start: '2023-01-15', target_week_end: '2023-01-21', predicted_cases: 260, interval_low: 230, interval_high: 290, reference_cases: 226.2, change_vs_reference_pct: 15, trend: 'aumento', observed_cases: null, absolute_error: null },
  ],
  comparison: [],
  reference: { description: 'x', value: 226.2 },
  history: [{ year: 2022, week: 52, week_end: '2022-12-31', cases: 178, status: 'OBSERVADO' }],
  variables: [
    { key: 'ira_history', description: 'x', used: true, available_for_municipality: true, available_at_origin: true, historical_coverage_pct: 99.7 },
    { key: 'precipitation', description: 'x', used: false, available_for_municipality: true, available_at_origin: true, historical_coverage_pct: 97 },
    { key: 'temperature', description: 'x', used: false, available_for_municipality: false, available_at_origin: false, historical_coverage_pct: 0 },
  ],
  coverage: { observed_weeks_last_52_pct: 100, observed_weeks_total_pct: 99.7, missing_prior_weeks_of_4: 0 },
  evaluation: {
    '2': { validation_2019: block, test_2022: block, pandemic_2020_2021: block },
    '3': { validation_2019: block, test_2022: block, pandemic_2020_2021: block },
  },
  warnings: [{ code: 'low_volume', message: 'fallback', params: { median: 6 } }],
  disclaimer: 'x',
}

const summary: ForecastModelsSummary = {
  models: [], trained_at: '2026-11-09', disclaimer: 'x',
  climate_contribution: [{ modelo: 'modelo_a', base: 'base_a', horizonte: 2, periodo: 'prueba_2022', n: 1820, mae_con_clima: 4.759, mae_base: 4.751, mejora_mae_pct: -0.2 }],
}

describe('ForecastPage', () => {
  beforeEach(() => {
    vi.mocked(forecastService.fetchForecastMunicipalities).mockResolvedValue(municipalities)
    vi.mocked(forecastService.fetchForecastModels).mockResolvedValue(summary)
    vi.mocked(forecastService.fetchForecast).mockResolvedValue(result)
  })

  it('responde en lenguaje claro: horizontes, tendencia, confianza y avisos', async () => {
    render(<ForecastPage />)

    expect(await screen.findByText('Dentro de 2 semanas')).toBeInTheDocument()
    expect(screen.getByText('Dentro de 3 semanas')).toBeInTheDocument()
    expect(screen.getByText(/Es una estimación de prueba/)).toBeInTheDocument()
    expect(screen.getByText(/no es un diagnóstico/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Se espera un nivel parecido al de las últimas semanas' })).toBeInTheDocument()
    expect(screen.getByText('Se mantiene')).toBeInTheDocument()
    expect(screen.getByText('Sube')).toBeInTheDocument()
    expect(screen.getByText(/Pocas atenciones por semana \(mediana de 6/)).toBeInTheDocument()
    expect(screen.getByText('Confianza baja')).toBeInTheDocument()
    expect(screen.getByText(/se desvió en promedio unas 4,2 atenciones por semana/)).toBeInTheDocument()
    expect(screen.getByText(/en 6 de cada 10 ocasiones/)).toBeInTheDocument()
    await waitFor(() => expect(forecastService.fetchForecast).toHaveBeenCalledWith('52001', { model: undefined }, expect.anything()))
  })

  it('oculta los detalles técnicos hasta que se piden', async () => {
    render(<ForecastPage />)

    const toggle = await screen.findByRole('button', { name: /Ver detalles técnicos/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText(/MAE persistencia/)).not.toBeInTheDocument()

    await userEvent.click(toggle)

    expect(screen.getByRole('button', { name: /Ocultar detalles técnicos/ })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Sin cobertura suficiente para este municipio')).toBeInTheDocument()
    expect(screen.getByText(/identificó solo el 7%/)).toBeInTheDocument()
    expect(screen.getAllByText('Modelo A · historial + precipitación').length).toBeGreaterThan(1)
  })

  it('avisa si los modelos no están entrenados', async () => {
    const { ApiError } = await import('../services/api')
    vi.mocked(forecastService.fetchForecastModels).mockRejectedValue(new ApiError('x', 503))

    render(<ForecastPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('La IA aún no está disponible')
  })

  it('el botón de recarga vuelve a consultar el análisis', async () => {
    render(<ForecastPage />)
    await screen.findByText('Dentro de 2 semanas')
    expect(forecastService.fetchForecast).toHaveBeenCalledTimes(1)

    await userEvent.click(screen.getByRole('button', { name: 'Recargar análisis' }))

    await waitFor(() => expect(forecastService.fetchForecast).toHaveBeenCalledTimes(2))
    expect(forecastService.fetchForecastMunicipalities).toHaveBeenCalledTimes(2)
    expect(await screen.findByText('Dentro de 2 semanas')).toBeInTheDocument()
  })

  it('mantiene el análisis fijo mientras se actualiza, sin reemplazarlo por la carga', async () => {
    render(<ForecastPage />)
    await screen.findByText('Dentro de 2 semanas')

    // La segunda consulta queda pendiente: el análisis anterior debe seguir visible y marcado como "actualizando".
    vi.mocked(forecastService.fetchForecast).mockReturnValue(new Promise(() => undefined))
    await userEvent.click(screen.getByRole('button', { name: 'Recargar análisis' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Actualizando el análisis')
    expect(screen.getByText('Dentro de 2 semanas')).toBeInTheDocument()
    expect(screen.queryByText('Obteniendo información...')).not.toBeInTheDocument()
  })

  it('si el análisis no responde, deja de cargar, avisa y permite reintentar', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      vi.mocked(forecastService.fetchForecast).mockReturnValue(new Promise(() => undefined))
      render(<ForecastPage />)

      await vi.advanceTimersByTimeAsync(30_000)

      expect(await screen.findByRole('alert')).toHaveTextContent('tardó demasiado en responder')
      expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })

  it('sin municipios no se queda cargando', async () => {
    vi.mocked(forecastService.fetchForecastMunicipalities).mockResolvedValue([])

    render(<ForecastPage />)

    expect(await screen.findByText('No hay datos disponibles.')).toBeInTheDocument()
    expect(screen.queryByText('Obteniendo información...')).not.toBeInTheDocument()
  })
})
