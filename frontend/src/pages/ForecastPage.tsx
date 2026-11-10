import {
  ArrowDownRight,
  ArrowUpRight,
  CalendarCheck,
  CalendarDays,
  ChartColumn,
  ChevronDown,
  CloudRain,
  FlaskConical,
  Gauge,
  History,
  Info,
  Minus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
  Thermometer,
  TrendingUp,
  TriangleAlert,
  Waves,
  type LucideIcon,
} from 'lucide-react'
import { useEffect, useId, useMemo, useState } from 'react'
import { ForecastChart } from '../components/forecast/ForecastChart'
import { Button } from '../components/common/Button'
import { Card } from '../components/common/Card'
import { EmptyState, ErrorState } from '../components/common/Feedback'
import { FilterBar, FilterField } from '../components/common/Filters'
import { Loading } from '../components/common/Loading'
import { PageHeader } from '../components/common/PageHeader'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import { ApiError } from '../services/api'
import { fetchForecast, fetchForecastModels, fetchForecastMunicipalities } from '../services/forecastService'
import type {
  ForecastEvalBlock,
  ForecastModelId,
  ForecastModelsSummary,
  ForecastMunicipality,
  ForecastPrediction,
  ChannelZone,
  ForecastResult,
  ForecastWarning,
  SignalLevel,
  Trend,
} from '../types/forecast'

const TREND_STYLE: Record<Trend, { badge: string; icon: typeof Minus; key: TranslationKey }> = {
  aumento: { badge: 'bg-rose-100 text-rose-900', icon: ArrowUpRight, key: 'fc.trend.aumento' },
  estable: { badge: 'bg-slate-100 text-slate-700', icon: Minus, key: 'fc.trend.estable' },
  disminucion: { badge: 'bg-emerald-100 text-emerald-900', icon: ArrowDownRight, key: 'fc.trend.disminucion' },
  sin_referencia: { badge: 'bg-slate-100 text-slate-700', icon: Minus, key: 'fc.trend.sin_referencia' },
}

const WARNING_KEYS: Record<string, TranslationKey> = {
  missing_lags: 'fc.warn.missing_lags',
  missing_precipitation: 'fc.warn.missing_precipitation',
  missing_temperature: 'fc.warn.missing_temperature',
  missing_consultations: 'fc.warn.missing_consultations',
  low_volume: 'fc.warn.low_volume',
  pandemic: 'fc.warn.pandemic',
  calendar_unverified: 'fc.warn.calendar_unverified',
  repeated_reports: 'fc.warn.repeated_reports',
}

// Cada aviso lleva su propio icono para reconocerlo de un vistazo sin leer todo el texto.
const WARNING_ICONS: Record<string, LucideIcon> = {
  missing_lags: History,
  missing_precipitation: CloudRain,
  missing_temperature: Thermometer,
  low_volume: ChartColumn,
  pandemic: ShieldAlert,
  calendar_unverified: CalendarDays,
  repeated_reports: TriangleAlert,
}

// Avisos que restan precisión a la estimación. La confianza nunca se presenta como "alta": la evaluación
// muestra que el modelo anticipa pocos de los aumentos reales, por eso el máximo es "media".
const CONFIDENCE_WARNINGS = new Set([
  'missing_lags',
  'missing_precipitation',
  'missing_temperature',
  'low_volume',
  'pandemic',
  'repeated_reports',
])

type Confidence = 'medium' | 'low'

function confidenceLevel(warnings: ForecastWarning[]): Confidence {
  return warnings.some((warning) => CONFIDENCE_WARNINGS.has(warning.code)) ? 'low' : 'medium'
}

const VARIABLE_KEYS = {
  ira_history: 'fc.var.ira_history',
  precipitation: 'fc.var.precipitation',
  temperature: 'fc.var.temperature',
} as const

function TrendBadge({ trend, suffix }: { trend: Trend; suffix?: string }) {
  const { t } = useI18n()
  const style = TREND_STYLE[trend]
  const Icon = style.icon
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${style.badge}`}>
      <Icon size={14} aria-hidden="true" />
      {t(style.key)}
      {suffix && <span className="tabular-nums opacity-90">· {suffix}</span>}
    </span>
  )
}

function PredictionCard({ prediction }: { prediction: ForecastPrediction }) {
  const { t, locale } = useI18n()
  const n = (value: number) => value.toLocaleString(locale, { maximumFractionDigits: 1 })
  return (
    <Card className="relative overflow-hidden p-5 sm:p-6">
      <span className="absolute inset-x-0 top-0 h-1 bg-amber-500" aria-hidden="true" />
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-respira-muted">{t('fc.horizonCard', { n: prediction.horizon_weeks })}</p>
          <p className="mt-3 text-3xl font-extrabold tracking-tight text-respira-text">
            ≈ {n(prediction.predicted_cases)}
          </p>
          <p className="mt-2 text-xs text-respira-muted">
            {t('fc.interval', { low: n(prediction.interval_low), high: n(prediction.interval_high) })}
          </p>
          <p className="mt-1 text-xs text-respira-muted">
            {t('fc.targetWeek', { week: prediction.target_week, year: prediction.target_year })}
          </p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
          <CalendarDays size={20} aria-hidden="true" />
        </span>
      </div>
      {prediction.observed_cases !== null && (
        <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900">
          {t('fc.observedAfter', { value: n(prediction.observed_cases), error: n(prediction.absolute_error ?? 0) })}
        </p>
      )}
    </Card>
  )
}

function TrendCard({ predictions }: { predictions: ForecastPrediction[] }) {
  const { t, locale } = useI18n()
  const n = (value: number) => value.toLocaleString(locale, { maximumFractionDigits: 1 })
  return (
    <Card className="relative overflow-hidden p-5 sm:p-6">
      <span className="absolute inset-x-0 top-0 h-1 bg-rose-600" aria-hidden="true" />
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-respira-muted">{t('fc.trendCard')}</p>
          <ul className="mt-3 space-y-2">
            {predictions.map((prediction) => {
              const change = prediction.change_vs_reference_pct
              return (
                <li key={prediction.horizon_weeks} className="flex flex-col items-start gap-1">
                  <span className="text-xs text-respira-muted">{t('fc.trendAt', { n: prediction.horizon_weeks })}</span>
                  <TrendBadge
                    trend={prediction.trend}
                    suffix={change === null ? undefined : `${change > 0 ? '+' : ''}${n(change)}%`}
                  />
                </li>
              )
            })}
          </ul>
          <p className="mt-3 text-xs text-respira-muted">{t('fc.vsReferenceNote')}</p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-800">
          <Gauge size={20} aria-hidden="true" />
        </span>
      </div>
    </Card>
  )
}

function ConfidenceCard({ data }: { data: ForecastResult }) {
  const { t, locale } = useI18n()
  const level = confidenceLevel(data.warnings)
  const filled = level === 'medium' ? 2 : 1
  const pct = data.coverage.observed_weeks_last_52_pct
  const goodCoverage = pct >= 90
  const test = data.evaluation['2']?.test_2022 ?? null
  const num = (value: number, digits = 0) =>
    value.toLocaleString(locale, { minimumFractionDigits: digits, maximumFractionDigits: digits })
  return (
    <Card className="flex flex-col gap-4 p-5 sm:p-6">
      <div>
        <h2 className="font-bold">{t('fc.confidenceTitle')}</h2>
        <p className="mt-1 text-xs text-respira-muted">{t('fc.confidenceSubtitle')}</p>
      </div>
      <div className="flex items-center gap-4 rounded-xl bg-respira-surface-alt px-4 py-3.5">
        <div className="flex items-end gap-1" aria-hidden="true">
          {[16, 24, 32].map((height, index) => (
            <span
              key={height}
              className={`w-2.5 rounded-[3px] ${index < filled ? 'bg-respira-blue' : 'bg-respira-field-border'}`}
              style={{ height }}
            />
          ))}
        </div>
        <div>
          <p className="text-lg font-extrabold text-respira-text">{t(`fc.confidence.${level}` as TranslationKey)}</p>
          <p className="text-sm text-respira-body">{t(`fc.confidenceHint.${level}` as TranslationKey)}</p>
        </div>
      </div>
      <p className="flex gap-2.5 text-sm leading-6">
        {goodCoverage ? (
          <ShieldCheck size={20} className="mt-0.5 shrink-0 text-emerald-800" aria-hidden="true" />
        ) : (
          <TriangleAlert size={20} className="mt-0.5 shrink-0 text-amber-700" aria-hidden="true" />
        )}
        <span>{t(goodCoverage ? 'fc.coverageGood' : 'fc.coverageLow', { pct: num(pct) })}</span>
      </p>
      {test && (
        <p className="flex gap-2.5 border-t border-respira-border pt-4 text-sm leading-6">
          <Target size={20} className="mt-0.5 shrink-0 text-sky-800" aria-hidden="true" />
          <span>{t('fc.pastTests', { mae: num(test.mae, 1), hits: Math.round(test.trend_accuracy * 10) })}</span>
        </p>
      )}
    </Card>
  )
}

const SIGNAL_STYLE: Record<SignalLevel, string> = {
  baja: 'bg-slate-100 text-slate-700',
  media: 'bg-amber-100 text-amber-950',
  alta: 'bg-rose-100 text-rose-900',
}

function IncreaseSignalCard({ data }: { data: ForecastResult }) {
  const { t, locale } = useI18n()
  if (!data.increase_signal?.length) return null
  const pct = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : Math.round(value * 100).toLocaleString(locale)
  const test = data.signal_evaluation?.['2']?.test_2022
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-bold">{t('fc.sigTitle')}</h2>
      <p className="mt-1 text-xs text-respira-muted">{t('fc.sigIntro')}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {data.increase_signal.map((signal) => (
          <div key={signal.horizon_weeks} className="rounded-xl border border-respira-border px-4 py-3.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-sm font-semibold text-respira-text">{t('fc.sigHorizon', { n: signal.horizon_weeks })}</span>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${SIGNAL_STYLE[signal.level]}`}>
                {t(`fc.sigLevel.${signal.level}` as TranslationKey)}
              </span>
            </div>
            <p className="mt-2 text-xs text-respira-muted">
              {t('fc.sigHistory', {
                level: t(`fc.sigWord.${signal.level}` as TranslationKey),
                rate: pct(signal.historical_increase_rate_for_level),
                base: pct(signal.base_increase_rate),
              })}
            </p>
            {signal.observed_increase !== null && (
              <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900">
                {signal.observed_increase ? t('fc.sigOutcomeYes') : t('fc.sigOutcomeNo')}
              </p>
            )}
          </div>
        ))}
      </div>
      {test && (
        <p className="mt-4 rounded-xl bg-amber-50 px-3.5 py-2.5 text-xs text-amber-950">
          {t('fc.sigCaveat', { precision: pct(test.high_precision), recall: pct(test.high_recall) })}
        </p>
      )}
    </Card>
  )
}

const ZONE_STYLE: Record<ChannelZone, string> = {
  dentro: 'bg-emerald-100 text-emerald-900',
  sobre: 'bg-amber-100 text-amber-950',
  alerta: 'bg-rose-100 text-rose-900',
}

function ChannelOutlookCard({ data }: { data: ForecastResult }) {
  const { t, locale } = useI18n()
  if (!data.channel_outlook?.length) return null
  const pct = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : Math.round(value * 100).toLocaleString(locale)
  const n = (value: number) => value.toLocaleString(locale, { maximumFractionDigits: 1 })
  const zoneName = (zone: ChannelZone) => t(`fc.chZone.${zone}` as TranslationKey)
  const test = data.channel_evaluation?.['2']?.p75.test_2022
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-bold">{t('fc.chTitle')}</h2>
      <p className="mt-1 text-xs text-respira-muted">{t('fc.chIntro')}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {data.channel_outlook.map((item) => {
          const predictions = data.predictions.find((p) => p.horizon_weeks === item.horizon_weeks)
          return (
            <div key={item.horizon_weeks} className="rounded-xl border border-respira-border px-4 py-3.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-semibold text-respira-text">
                  {t('fc.targetWeek', { week: item.target_week, year: item.target_year })}
                </span>
                {item.available && item.predicted_zone && (
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${ZONE_STYLE[item.predicted_zone]}`}>
                    {zoneName(item.predicted_zone)}
                  </span>
                )}
              </div>
              {!item.available || !item.channel ? (
                <p className="mt-2 text-xs text-respira-muted">{t('fc.chUnavailable')}</p>
              ) : (
                <>
                  <p className="mt-2 text-xs tabular-nums text-respira-muted">
                    {t('fc.chChannel', { p50: n(item.channel.p50), p75: n(item.channel.p75), p90: n(item.channel.p90) })}
                    {predictions ? ` · ${t('fc.chPredicted', { value: n(predictions.predicted_cases) })}` : ''}
                  </p>
                  {item.exceed_p75 && (
                    <p className="mt-2 text-xs text-respira-body">
                      {t('fc.chExceed75', {
                        level: t(`fc.sigWord.${item.exceed_p75.level}` as TranslationKey),
                        rate: pct(item.exceed_p75.historical_rate_for_level),
                        base: pct(item.exceed_p75.base_rate),
                      })}
                    </p>
                  )}
                  {item.exceed_p90 && (
                    <p className="mt-1.5 text-xs text-respira-body">
                      {t('fc.chExceed90', {
                        level: t(`fc.sigWord.${item.exceed_p90.level}` as TranslationKey),
                        rate: pct(item.exceed_p90.historical_rate_for_level),
                        base: pct(item.exceed_p90.base_rate),
                      })}
                    </p>
                  )}
                  {item.observed_zone && (
                    <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-900">
                      {t('fc.chObserved', { zone: zoneName(item.observed_zone).toLowerCase() })}
                    </p>
                  )}
                </>
              )}
            </div>
          )
        })}
      </div>
      {test && test.auc_simple_rule !== null && (
        <p className="mt-4 rounded-xl bg-amber-50 px-3.5 py-2.5 text-xs text-amber-950">
          {t('fc.chCaveat', {
            auc: test.auc.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
            simple: test.auc_simple_rule.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
          })}
        </p>
      )}
    </Card>
  )
}

function WarningList({ warnings }: { warnings: ForecastWarning[] }) {
  const { t } = useI18n()
  return (
    <ul className="space-y-2.5">
      {warnings.map((warning) => {
        const key = WARNING_KEYS[warning.code]
        const Icon = WARNING_ICONS[warning.code] ?? TriangleAlert
        return (
          <li
            key={warning.code}
            className="flex gap-2.5 rounded-xl bg-amber-50 px-3.5 py-3 text-sm leading-6 text-amber-950"
          >
            <Icon size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
            <span>{key ? t(key, warning.params) : warning.message}</span>
          </li>
        )
      })}
      {!warnings.length && <li className="text-sm text-respira-body">{t('fc.noWarnings')}</li>}
      <li className="flex gap-2.5 rounded-xl bg-sky-50 px-3.5 py-3 text-sm leading-6 text-respira-text">
        <Info size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
        <span>{t('fc.notExact')}</span>
      </li>
    </ul>
  )
}

function EvaluationTable({ data }: { data: ForecastResult }) {
  const { t, locale } = useI18n()
  const f = (value: number, digits = 2) => value.toLocaleString(locale, { minimumFractionDigits: digits, maximumFractionDigits: digits })
  const periods: Array<{ key: 'validation_2019' | 'test_2022' | 'pandemic_2020_2021'; label: TranslationKey }> = [
    { key: 'validation_2019', label: 'fc.period.validation' },
    { key: 'test_2022', label: 'fc.period.test' },
    { key: 'pandemic_2020_2021', label: 'fc.period.pandemic' },
  ]
  const testH2: ForecastEvalBlock | null = data.evaluation['2']?.test_2022 ?? null
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-bold">{t('fc.evalTitle')}</h2>
      <p className="mt-1 text-xs text-respira-muted">{t('fc.evalNote')}</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <thead className="text-xs text-respira-muted">
            <tr>
              <th className="py-2 pr-3 font-semibold">{t('fc.evalPeriod')}</th>
              <th className="py-2 pr-3 font-semibold">{t('fc.evalHorizon')}</th>
              <th className="py-2 pr-3 text-right font-semibold">n</th>
              <th className="py-2 pr-3 text-right font-semibold">MAE</th>
              <th className="py-2 pr-3 text-right font-semibold">RMSE</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('fc.evalPersistence')}</th>
              <th className="py-2 text-right font-semibold">{t('fc.evalGain')}</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {periods.flatMap((period) =>
              ['2', '3'].map((h) => {
                const block = data.evaluation[h]?.[period.key]
                if (!block) return null
                return (
                  <tr key={`${period.key}-${h}`} className="border-t border-respira-border">
                    <td className="py-2 pr-3 font-medium text-respira-text">{t(period.label)}</td>
                    <td className="py-2 pr-3">{t('fc.weeksN', { n: h })}</td>
                    <td className="py-2 pr-3 text-right">{block.n.toLocaleString(locale)}</td>
                    <td className="py-2 pr-3 text-right font-semibold text-respira-text">{f(block.mae)}</td>
                    <td className="py-2 pr-3 text-right">{f(block.rmse)}</td>
                    <td className="py-2 pr-3 text-right">{f(block.mae_persistence)}</td>
                    <td
                      className={`py-2 text-right font-semibold ${
                        block.improvement_vs_persistence_pct >= 0 ? 'text-emerald-800' : 'text-rose-800'
                      }`}
                    >
                      {block.improvement_vs_persistence_pct > 0 ? '+' : ''}
                      {f(block.improvement_vs_persistence_pct, 1)}%
                    </td>
                  </tr>
                )
              }),
            )}
          </tbody>
        </table>
      </div>
      {testH2?.increase_recall !== null && testH2?.increase_recall !== undefined && (
        <p className="mt-4 rounded-xl bg-amber-50 px-3.5 py-2.5 text-xs text-amber-950">
          {t('fc.evalCaveat', {
            recall: Math.round(testH2.increase_recall * 100),
            accuracy: Math.round(testH2.trend_accuracy * 100),
          })}
        </p>
      )}
    </Card>
  )
}

function ClimateContribution({ summary }: { summary: ForecastModelsSummary }) {
  const { t, locale } = useI18n()
  const rows = summary.climate_contribution.filter((row) => row.periodo === 'prueba_2022')
  const f = (value: number, digits = 2) => value.toLocaleString(locale, { minimumFractionDigits: digits, maximumFractionDigits: digits })
  const label = (id: string) => (id === 'modelo_a' ? t('fc.modelA') : t('fc.modelB'))
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-bold">{t('fc.climateTitle')}</h2>
      <p className="mt-1 text-xs text-respira-muted">{t('fc.climateNote')}</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[28rem] text-left text-sm">
          <thead className="text-xs text-respira-muted">
            <tr>
              <th className="py-2 pr-3 font-semibold">{t('fc.model')}</th>
              <th className="py-2 pr-3 font-semibold">{t('fc.evalHorizon')}</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('fc.maeClimate')}</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('fc.maeBase')}</th>
              <th className="py-2 text-right font-semibold">{t('fc.evalGain')}</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {rows.map((row) => (
              <tr key={`${row.modelo}-${row.horizonte}`} className="border-t border-respira-border">
                <td className="py-2 pr-3 font-medium text-respira-text">{label(row.modelo)}</td>
                <td className="py-2 pr-3">{t('fc.weeksN', { n: row.horizonte })}</td>
                <td className="py-2 pr-3 text-right">{f(row.mae_con_clima)}</td>
                <td className="py-2 pr-3 text-right">{f(row.mae_base)}</td>
                <td className={`py-2 text-right font-semibold ${row.mejora_mae_pct >= 0 ? 'text-emerald-800' : 'text-rose-800'}`}>
                  {row.mejora_mae_pct > 0 ? '+' : ''}
                  {f(row.mejora_mae_pct, 1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}


function DataExtension({ summary }: { summary: ForecastModelsSummary }) {
  const { t } = useI18n()
  const ext = summary.data_extension
  if (!ext) return null
  const m = (key: string) => ext.climate_public[key]?.municipalities ?? 0
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-bold">{t('fc.extTitle')}</h2>
      <p className="mt-1 text-xs text-respira-muted">{t('fc.extIntro')}</p>
      <ul className="mt-4 list-disc space-y-1.5 pl-5 text-sm text-respira-body">
        <li>{t('fc.extPopulation', { year: ext.population_through_year })}</li>
        <li>{t('fc.extCalendar', { weeks: ext.calendar_weeks['2025'] ?? '—', anchors: ext.calendar_ins_anchors.length })}</li>
        <li>
          {t('fc.extClimate', { temp: m('temp_media'), hum: m('humedad_relativa'), prec: m('precipitacion') })}
        </li>
      </ul>
    </Card>
  )
}

// Tiempo máximo de espera del análisis. En Electron la consulta pasa por el proceso principal y no se puede
// cancelar con AbortController, así que sin este límite una respuesta que nunca llega dejaba la pantalla cargando.
const LOAD_TIMEOUT_MS = 30_000

class LoadTimeoutError extends Error {}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new LoadTimeoutError('timeout')), ms)
    promise.then(resolve, reject).finally(() => window.clearTimeout(timer))
  })
}

export function ForecastPage() {
  const { t, locale } = useI18n()
  const detailsId = useId()
  const [municipalities, setMunicipalities] = useState<ForecastMunicipality[]>([])
  const [code, setCode] = useState<string>('')
  const [origin, setOrigin] = useState<{ year: number; week: number } | undefined>()
  const [model, setModel] = useState<ForecastModelId | undefined>()
  const [data, setData] = useState<ForecastResult | null>(null)
  const [originOptions, setOriginOptions] = useState<Array<{ year: number; week: number }>>([])
  const [summary, setSummary] = useState<ForecastModelsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  // Cambia cada vez que se pide recargar; las consultas dependen de este valor y se repiten.
  const [reloadKey, setReloadKey] = useState(0)

  const reload = () => {
    setError(null)
    setLoading(true)
    setReloadKey((current) => current + 1)
  }

  const failure = (reason: unknown, notFoundKey: TranslationKey = 'fc.loadError') =>
    reason instanceof LoadTimeoutError
      ? t('fc.timeout')
      : reason instanceof ApiError && reason.status === 503
        ? t('fc.notReady')
        : reason instanceof ApiError && (reason.status === 404 || reason.status === 422)
          ? t(notFoundKey)
          : t('fc.loadError')

  useEffect(() => {
    const controller = new AbortController()
    withTimeout(
      Promise.all([fetchForecastMunicipalities(controller.signal), fetchForecastModels(controller.signal)]),
      LOAD_TIMEOUT_MS,
    )
      .then(([list, models]) => {
        if (controller.signal.aborted) return
        setMunicipalities(list)
        setSummary(models)
        const first = (list.find((item) => item.divipola_code === '52001') ?? list[0])?.divipola_code ?? ''
        setCode((current) => current || first)
        // Sin municipios no habrá segunda consulta: se quita la carga para que no quede esperando para siempre.
        if (!first) setLoading(false)
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return
        setError(failure(reason))
        setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey])

  useEffect(() => {
    if (!code) return
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    withTimeout(fetchForecast(code, { ...origin, model }, controller.signal), LOAD_TIMEOUT_MS)
      .then((result) => {
        if (controller.signal.aborted) return
        setData(result)
        if (result.origin.is_latest_available) {
          setOriginOptions(
            result.history
              .filter((point) => point.cases !== null && point.year === result.origin.year)
              .map((point) => ({ year: point.year, week: point.week }))
              .reverse(),
          )
        }
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return
        setData(null)
        setError(failure(reason, 'fc.originError'))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, origin, model, reloadKey])

  const selected = useMemo(() => municipalities.find((item) => item.divipola_code === code), [municipalities, code])
  const modelLabel = (id: ForecastModelId) =>
    id === 'base_global' ? t('fc.modelBase') : id === 'modelo_a' ? t('fc.modelA') : t('fc.modelB')
  const n = (value: number | null | undefined) =>
    value === null || value === undefined ? '—' : value.toLocaleString(locale, { maximumFractionDigits: 1 })

  const headlineTrend: Trend = data?.predictions[0]?.trend ?? 'sin_referencia'
  // El análisis ya mostrado se queda fijo en pantalla mientras se actualiza (atenuado), en lugar de desaparecer.
  const refreshing = loading && data !== null

  const steps: Array<{ icon: LucideIcon; title: TranslationKey; text: TranslationKey }> = [
    { icon: History, title: 'fc.how1Title', text: 'fc.how1Text' },
    { icon: CloudRain, title: 'fc.how2Title', text: 'fc.how2Text' },
    { icon: TrendingUp, title: 'fc.how3Title', text: 'fc.how3Text' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('fc.eyebrow')}
        title={t('fc.title')}
        icon={Sparkles}
        description={t('fc.description')}
        actions={
          <>
            {refreshing && (
              <span className="text-sm text-respira-muted" role="status">
                {t('fc.reloading')}
              </span>
            )}
            <Button type="button" variant="secondary" onClick={reload} aria-busy={loading} className="min-h-11">
              <RefreshCw size={17} className={loading ? 'animate-spin' : ''} aria-hidden="true" />
              {t('fc.reload')}
            </Button>
          </>
        }
      />
      <div
        className="flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950"
        role="note"
      >
        <FlaskConical size={18} className="mt-1 shrink-0" aria-hidden="true" />
        <p>
          <strong>{t('fc.experimental')}</strong> {t('fc.disclaimer')}
        </p>
      </div>

      <FilterBar note={t('fc.filterNote')}>
        <FilterField label={t('fc.askMunicipality')}>
          <select
            className="field-control min-w-56"
            value={code}
            onChange={(event) => {
              setCode(event.target.value)
              setOrigin(undefined)
              setModel(undefined)
              setOriginOptions([])
            }}
          >
            {municipalities.map((item) => (
              <option key={item.divipola_code} value={item.divipola_code}>
                {item.name}
              </option>
            ))}
          </select>
        </FilterField>
        <FilterField label={t('fc.referenceWeek')}>
          <select
            className="field-control"
            value={origin ? `${origin.year}-${origin.week}` : ''}
            onChange={(event) => {
              const [year, week] = event.target.value.split('-').map(Number)
              setOrigin(event.target.value ? { year, week } : undefined)
            }}
          >
            <option value="">{t('fc.latestWeek')}</option>
            {originOptions.map((option) => (
              <option key={`${option.year}-${option.week}`} value={`${option.year}-${option.week}`}>
                {t('fc.weekOfYear', { week: option.week, year: option.year })}
              </option>
            ))}
          </select>
        </FilterField>
      </FilterBar>

      {loading && !data ? (
        <Card>
          <Loading />
        </Card>
      ) : error ? (
        <Card>
          <ErrorState message={error} />
          <div className="flex justify-center pb-6">
            <Button type="button" onClick={reload}>
              <RefreshCw size={16} aria-hidden="true" />
              {t('fc.retry')}
            </Button>
          </div>
        </Card>
      ) : !data ? (
        <Card>
          <EmptyState>{t('common.noData')}</EmptyState>
        </Card>
      ) : (
        <div
          aria-busy={refreshing}
          className={`space-y-6 transition-opacity ${refreshing ? 'pointer-events-none opacity-60' : ''}`}
        >
          <Card className="relative flex items-center gap-4 overflow-hidden p-5 sm:px-6">
            <span className="absolute inset-x-0 top-0 h-1 bg-respira-blue" aria-hidden="true" />
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
              <TrendingUp size={20} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-respira-muted">{t('fc.answerLabel')}</p>
              <h2 className="mt-1 text-[22px] font-extrabold leading-tight tracking-tight">
                {t(`fc.answer.${headlineTrend}` as TranslationKey)}
              </h2>
              <p className="mt-1.5 text-sm leading-6 text-respira-body">
                {t('fc.summaryNow', {
                  week: data.origin.week,
                  year: data.origin.year,
                  value: n(data.origin.observed_cases),
                })}{' '}
                {data.predictions
                  .map((prediction) =>
                    t('fc.summaryHorizon', { n: prediction.horizon_weeks, value: n(prediction.predicted_cases) }),
                  )
                  .join(' ')}
              </p>
            </div>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="relative overflow-hidden p-5 sm:p-6">
              <span className="absolute inset-x-0 top-0 h-1 bg-respira-blue" aria-hidden="true" />
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-respira-muted">{t('fc.thisWeek')}</p>
                  <p className="mt-3 text-3xl font-extrabold tracking-tight text-respira-text">
                    {n(data.origin.observed_cases)}
                  </p>
                  <p className="mt-2 text-xs text-respira-muted">{t('fc.thisWeekNote', { week: data.origin.week })}</p>
                  <p className="mt-1 text-xs text-respira-muted">{t('fc.referenceAvg', { value: n(data.reference.value) })}</p>
                </div>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
                  <CalendarCheck size={20} aria-hidden="true" />
                </span>
              </div>
            </Card>
            {data.predictions.map((prediction) => (
              <PredictionCard key={prediction.horizon_weeks} prediction={prediction} />
            ))}
            <TrendCard predictions={data.predictions} />
          </div>

          <IncreaseSignalCard data={data} />

          <ChannelOutlookCard data={data} />

          <ForecastChart data={data} />

          <div className="grid gap-6 xl:grid-cols-2">
            <ConfidenceCard data={data} />
            <Card className="p-5 sm:p-6">
              <h2 className="font-bold">{t('fc.warnTitle')}</h2>
              <p className="mt-1 text-xs text-respira-muted">{t('fc.warnSubtitle')}</p>
              <div className="mt-4">
                <WarningList warnings={data.warnings} />
              </div>
            </Card>
          </div>

          <Card className="p-5 sm:p-6">
            <h2 className="font-bold">{t('fc.howTitle')}</h2>
            <ol className="mt-4 grid list-none gap-5 p-0 md:grid-cols-3">
              {steps.map(({ icon: Icon, title, text }) => (
                <li key={title} className="flex items-start gap-3">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
                    <Icon size={20} aria-hidden="true" />
                  </span>
                  <p className="text-sm leading-6 text-respira-body">
                    <strong className="text-respira-text">{t(title)}</strong> {t(text)}
                  </p>
                </li>
              ))}
            </ol>
          </Card>

          <Card className="overflow-hidden">
            <h2>
              <button
                type="button"
                aria-expanded={showDetails}
                aria-controls={detailsId}
                onClick={() => setShowDetails((current) => !current)}
                className="flex min-h-16 w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-sky-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-respira-blue-dark sm:px-6"
              >
                <span className="flex flex-col gap-0.5">
                  <span className="font-bold">{showDetails ? t('fc.detailsHide') : t('fc.detailsShow')}</span>
                  <span className="text-xs font-normal text-respira-muted">{t('fc.detailsHint')}</span>
                </span>
                <ChevronDown
                  size={22}
                  aria-hidden="true"
                  className={`shrink-0 transition-transform ${showDetails ? 'rotate-180' : ''}`}
                />
              </button>
            </h2>
            {showDetails && (
              <div id={detailsId} className="space-y-6 border-t border-respira-border p-5 sm:p-6">
                <div className="grid gap-6 xl:grid-cols-2">
                  <div className="space-y-4">
                    <FilterField label={t('fc.model')}>
                      <select
                        className="field-control min-w-64"
                        value={model ?? selected?.default_model ?? 'base_global'}
                        onChange={(event) => setModel(event.target.value as ForecastModelId)}
                      >
                        {(selected?.available_models ?? ['base_global']).map((id) => (
                          <option key={id} value={id}>
                            {modelLabel(id)}
                            {id === selected?.default_model ? ` · ${t('fc.recommended')}` : ''}
                          </option>
                        ))}
                      </select>
                    </FilterField>
                    <h3 className="flex items-center gap-2 text-sm font-bold">
                      <Waves size={18} className="text-sky-800" aria-hidden="true" />
                      {t('fc.coverageTitle')}
                    </h3>
                    <p className="text-xs text-respira-muted">
                      {t('fc.modelUsed', { label: modelLabel(data.model.id) })} ·{' '}
                      {t('fc.coverageWeeks', { pct: n(data.coverage.observed_weeks_last_52_pct) })}
                    </p>
                    <ul className="space-y-3">
                      {data.variables.map((variable) => (
                        <li key={variable.key} className="rounded-xl border border-respira-border px-3.5 py-3 text-sm">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-semibold text-respira-text">{t(VARIABLE_KEYS[variable.key])}</span>
                            <span
                              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                                variable.used ? 'bg-sky-100 text-sky-900' : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {variable.used ? t('fc.varUsed') : t('fc.varNotUsed')}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-respira-muted">
                            {!variable.available_for_municipality
                              ? t('fc.varUnavailable')
                              : variable.available_at_origin
                                ? t('fc.varAtOrigin')
                                : t('fc.varMissing')}
                            {variable.available_for_municipality &&
                              ` · ${t('fc.histCoverage', { pct: n(variable.historical_coverage_pct) })}`}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                  {data.comparison.length > 0 && (
                    <div>
                      <h3 className="text-sm font-bold">{t('fc.compareTitle')}</h3>
                      <ul className="mt-3 space-y-2 text-sm">
                        {data.comparison.map((other) => (
                          <li key={other.model} className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-respira-body">{modelLabel(other.model)}</span>
                            <span className="tabular-nums text-respira-text">
                              {other.predictions.map((p) => `+${p.horizon_weeks}s: ${n(p.predicted_cases)}`).join(' · ')}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <EvaluationTable data={data} />
                {summary && <ClimateContribution summary={summary} />}
          {summary && <DataExtension summary={summary} />}

                <div className="rounded-xl bg-respira-surface-alt px-4 py-3.5 text-sm leading-6 text-respira-body">
                  <p className="font-bold text-respira-text">{t('fc.glossaryTitle')}</p>
                  <p className="mt-1">{t('fc.glossaryText')}</p>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
