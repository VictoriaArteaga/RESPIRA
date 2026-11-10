import { Activity, ArrowRight, Bell, ChartLine, LogIn, Lock, Map as MapIcon, UserPlus, type LucideIcon } from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'
import { RiskBadge } from '../components/common/RiskBadge'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import { usePreferences } from '../preferences/PreferencesContext'

const focusRing =
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-respira-blue-dark'
const primaryLink = `inline-flex items-center justify-center gap-2 rounded-xl bg-respira-blue text-white transition-colors hover:bg-respira-blue-dark ${focusRing}`
const secondaryLink = `inline-flex items-center justify-center gap-2 rounded-xl border border-respira-border bg-respira-surface text-respira-text transition-colors hover:bg-sky-50 ${focusRing}`
const card = 'rounded-2xl border border-respira-border bg-respira-surface shadow-card'
const sectionWidth = 'mx-auto w-full max-w-[1200px] px-8'

const features: { icon: LucideIcon; title: TranslationKey; text: TranslationKey }[] = [
  { icon: MapIcon, title: 'nav.riskMap', text: 'landing.featureMapText' },
  { icon: ChartLine, title: 'nav.endemic', text: 'landing.featureEndemicText' },
  { icon: Bell, title: 'nav.alerts', text: 'landing.featureAlertsText' },
  { icon: Activity, title: 'landing.featureCasesTitle', text: 'landing.featureCasesText' },
]

const steps: { title: TranslationKey; text: TranslationKey }[] = [
  { title: 'landing.step1Title', text: 'landing.step1Text' },
  { title: 'landing.step2Title', text: 'landing.step2Text' },
  { title: 'landing.step3Title', text: 'landing.step3Text' },
]

const levels: { level: 'low' | 'moderate' | 'high'; text: TranslationKey }[] = [
  { level: 'low', text: 'landing.levelLow' },
  { level: 'moderate', text: 'landing.levelModerate' },
  { level: 'high', text: 'landing.levelHigh' },
]

// Ilustración con datos inventados: no representa información real de ningún municipio.
function EndemicIllustration() {
  const { t } = useI18n()
  return (
    <svg viewBox="0 0 300 160" width="100%" role="img" aria-label={t('landing.chartAlt')} className="block">
      <polygon
        className="fill-sky-50"
        points="34,78 57.3,74 80.5,70 103.8,60 127.1,52 150.4,48 173.6,56 196.9,66 220.2,72 243.5,78 266.7,82 290,84 290,102 266.7,100 243.5,96 220.2,92 196.9,86 173.6,76 150.4,68 127.1,72 103.8,80 80.5,88 57.3,92 34,96"
      />
      <polygon
        className="fill-sky-100"
        points="34,96 57.3,92 80.5,88 103.8,80 127.1,72 150.4,68 173.6,76 196.9,86 220.2,92 243.5,96 266.7,100 290,102 290,124 266.7,122 243.5,120 220.2,118 196.9,114 173.6,110 150.4,106 127.1,108 103.8,112 80.5,116 57.3,118 34,120"
      />
      <polyline
        className="stroke-sky-200"
        fill="none"
        strokeWidth="1"
        points="34,78 57.3,74 80.5,70 103.8,60 127.1,52 150.4,48 173.6,56 196.9,66 220.2,72 243.5,78 266.7,82 290,84"
      />
      <line x1="34" y1="130" x2="290" y2="130" className="stroke-respira-muted" strokeWidth="1" />
      <line x1="34" y1="10" x2="34" y2="130" className="stroke-respira-muted" strokeWidth="1" />
      <polyline
        className="stroke-respira-link"
        fill="none"
        strokeWidth="1.5"
        strokeDasharray="5 4"
        points="34,108 57.3,104 80.5,100 103.8,94 127.1,88 150.4,84 173.6,90 196.9,98 220.2,104 243.5,108 266.7,112 290,114"
      />
      <polyline
        className="stroke-respira-blue"
        fill="none"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points="34,112 57.3,106 80.5,98 103.8,84 127.1,62 150.4,30 173.6,48 196.9,70 220.2,94 243.5,106 266.7,114 290,116"
      />
      {[
        [34, 112],
        [80.5, 98],
        [127.1, 62],
        [196.9, 70],
        [243.5, 106],
        [290, 116],
      ].map(([cx, cy]) => (
        <circle key={cx} cx={cx} cy={cy} r="3" className="fill-respira-blue stroke-respira-surface" strokeWidth="1.5" />
      ))}
      <circle cx="150.4" cy="30" r="9" className="fill-rose-600" opacity=".18" />
      <circle cx="150.4" cy="30" r="5" className="fill-rose-600 stroke-respira-surface" strokeWidth="2" />
      <text x="162" y="26" fontSize="10" fontWeight="600" className="fill-rose-700">
        {t('landing.chartPeak')}
      </text>
      <text x="4" y="14" fontSize="10" className="fill-respira-muted">
        {t('landing.chartCases')}
      </text>
      <g fontSize="10" textAnchor="middle" className="fill-respira-muted">
        <text x="34" y="146">{t('landing.chartMonth1')}</text>
        <text x="103.8" y="146">{t('landing.chartMonth4')}</text>
        <text x="173.6" y="146">{t('landing.chartMonth7')}</text>
        <text x="243.5" y="146">{t('landing.chartMonth10')}</text>
      </g>
    </svg>
  )
}

export function LandingPage() {
  const { status } = useAuth()
  const { startPage } = usePreferences()
  const { t } = useI18n()

  // Con sesión activa la pantalla informativa no aporta: se entra directo a la página de inicio elegida.
  if (status === 'authenticated') return <Navigate to={startPage} replace />

  const navLink = `px-2.5 py-3 text-sm font-semibold text-respira-body hover:text-respira-blue-dark ${focusRing}`

  return (
    <div className="app-shell text-respira-text">
      <header className="border-b border-respira-border bg-respira-chrome">
        <div className={`${sectionWidth} flex flex-wrap items-center justify-between gap-3 py-3.5`}>
          <Link to="/" aria-label={t('landing.homeAria')} className={`flex items-center gap-3 rounded-xl ${focusRing}`}>
            <span
              aria-hidden="true"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-respira-blue text-[22px] font-black text-white shadow-[0_4px_10px_rgba(49,95,125,0.25)]"
            >
              R
            </span>
            <span className="text-xl font-extrabold tracking-tight">RESPIRA</span>
          </Link>
          <nav aria-label={t('landing.navAria')} className="flex flex-wrap items-center gap-2">
            <a href="#que-es" className={navLink}>{t('landing.navWhat')}</a>
            <a href="#funciones" className={navLink}>{t('landing.navFeatures')}</a>
            <a href="#niveles" className={navLink}>{t('landing.navLevels')}</a>
            <Link to="/login" className={`${secondaryLink} min-h-11 px-4 text-sm font-semibold`}>
              {t('auth.login')}
            </Link>
            <Link to="/register" className={`${primaryLink} min-h-11 px-4 text-sm font-semibold`}>
              {t('auth.registerLink')}
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className={`${sectionWidth} flex flex-wrap items-center gap-12 pb-20 pt-[72px]`}>
          <div className="flex min-w-0 flex-[1_1_440px] flex-col gap-5">
            <p className="text-[13px] font-bold tracking-[0.16em] text-respira-link">RESPIRA</p>
            <h1 className="text-[46px] font-extrabold leading-[1.1] tracking-tight">{t('landing.heroTitle')}</h1>
            <p className="max-w-[520px] text-[17px] leading-relaxed text-respira-body">{t('landing.heroText')}</p>
            <div className="mt-2 flex flex-wrap gap-3">
              <Link
                to="/login"
                className={`${primaryLink} min-h-[50px] px-6 text-base font-bold shadow-[0_4px_14px_rgba(49,95,125,0.25)]`}
              >
                <LogIn size={19} aria-hidden="true" />
                {t('auth.login')}
              </Link>
              <Link to="/register" className={`${secondaryLink} min-h-[50px] px-6 text-base font-bold`}>
                <UserPlus size={19} aria-hidden="true" />
                {t('auth.requestAccount')}
              </Link>
            </div>
            <p className="flex items-center gap-2 text-[13px] text-respira-muted">
              <Lock size={16} aria-hidden="true" className="flex-none" />
              {t('landing.approvalNote')}
            </p>
          </div>

          <div className="min-w-0 flex-[1_1_420px]">
            <figure className={`${card} mx-auto max-w-[480px] p-6 shadow-[0_12px_36px_rgba(36,59,74,0.10)]`}>
              <figcaption className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <span className="text-base font-bold">{t('nav.endemic')}</span>
                <RiskBadge level="high" />
              </figcaption>
              <EndemicIllustration />
              <ul className="mt-1.5 flex list-none flex-wrap gap-x-3.5 gap-y-1.5 p-0 text-[11px] text-respira-body">
                <li className="flex items-center gap-1.5">
                  <span aria-hidden="true" className="h-[3px] w-3.5 rounded-sm bg-respira-blue" />
                  {t('landing.chartObserved')}
                </li>
                <li className="flex items-center gap-1.5">
                  <span aria-hidden="true" className="w-3.5 border-t-2 border-dashed border-respira-link" />
                  {t('landing.chartMedian')}
                </li>
                <li className="flex items-center gap-1.5">
                  <span aria-hidden="true" className="h-[9px] w-3.5 bg-sky-100" />
                  P25–P75
                </li>
                <li className="flex items-center gap-1.5">
                  <span aria-hidden="true" className="h-[9px] w-3.5 border-t border-sky-200 bg-sky-50" />
                  P75–P90
                </li>
                <li className="ml-auto text-respira-muted">{t('landing.illustration')}</li>
              </ul>
            </figure>
          </div>
        </section>

        <section id="que-es" className={`${sectionWidth} pb-[72px]`}>
          <div className="flex flex-wrap overflow-hidden rounded-[20px] border border-respira-border bg-respira-surface shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
            <div className="flex min-w-0 flex-[1_1_340px] flex-col justify-between gap-5 bg-gradient-to-br from-[#315F7D] to-[#234A65] px-10 py-12 text-white">
              <div className="flex flex-col gap-5">
                <Activity size={40} aria-hidden="true" />
                <h2 className="text-[28px] font-extrabold leading-tight tracking-tight">{t('landing.whatTitle')}</h2>
                <p className="text-[15px] leading-[1.7] text-[#E6EFF5]">{t('landing.whatLead')}</p>
              </div>
              <div className="flex items-center gap-2.5 text-sm font-semibold">
                <Activity size={20} aria-hidden="true" className="flex-none" />
                <span>{t('layout.tagline')}</span>
              </div>
            </div>
            <div className="flex min-w-0 flex-[999_1_420px] flex-col gap-4 px-10 py-12">
              <p className="text-[15px] leading-[1.7] text-respira-body">{t('landing.whatP1')}</p>
              <p className="text-[15px] leading-[1.7] text-respira-body">{t('landing.whatP2')}</p>
              <p className="text-[13px] leading-relaxed text-respira-muted">{t('landing.whatP3')}</p>
            </div>
          </div>
        </section>

        <section id="como" className={`${sectionWidth} flex flex-col gap-7 pb-[72px]`}>
          <div className="flex flex-col gap-1.5">
            <h2 className="text-[30px] font-extrabold tracking-tight">{t('landing.stepsTitle')}</h2>
            <p className="text-sm text-respira-body">{t('landing.stepsSubtitle')}</p>
          </div>
          <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5 p-0">
            {steps.map((step, index) => (
              <li key={step.title} className={`${card} flex items-start gap-4 p-6`}>
                <span className="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-respira-blue text-base font-extrabold text-white">
                  {index + 1}
                </span>
                <div className="flex flex-col gap-1.5">
                  <h3 className="text-[17px] font-bold">{t(step.title)}</h3>
                  <p className="text-sm leading-relaxed text-respira-body">{t(step.text)}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section id="funciones" className={`${sectionWidth} flex flex-col gap-7 pb-[72px]`}>
          <div className="flex flex-col gap-1.5">
            <h2 className="text-[30px] font-extrabold tracking-tight">{t('landing.featuresTitle')}</h2>
            <p className="text-sm text-respira-body">{t('landing.featuresSubtitle')}</p>
          </div>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5">
            {features.map(({ icon: Icon, title, text }) => (
              <div key={title} className={`${card} flex flex-col gap-2.5 p-6`}>
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-50 text-respira-link">
                  <Icon size={22} aria-hidden="true" />
                </span>
                <h3 className="text-[17px] font-bold">{t(title)}</h3>
                <p className="text-sm leading-relaxed text-respira-body">{t(text)}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="niveles" className={`${sectionWidth} pb-[72px]`}>
          <div className={`${card} flex flex-col gap-5 p-8`}>
            <div className="flex flex-col gap-1.5">
              <h2 className="text-2xl font-extrabold tracking-tight">{t('landing.levelsTitle')}</h2>
              <p className="text-sm leading-relaxed text-respira-body">{t('landing.levelsText')}</p>
            </div>
            <ul className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4 p-0">
              {levels.map(({ level, text }) => (
                <li key={level} className="flex flex-col items-start gap-2 rounded-xl bg-respira-surface-alt p-4">
                  <RiskBadge level={level} />
                  <span className="text-sm text-respira-body">{t(text)}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className={`${sectionWidth} pb-[72px]`}>
          <div className="flex flex-wrap items-center justify-between gap-6 rounded-[20px] bg-gradient-to-br from-[#315F7D] to-[#234A65] p-10 text-white shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
            <div className="flex min-w-0 flex-[1_1_360px] flex-col gap-2">
              <h2 className="text-[28px] font-extrabold tracking-tight">{t('auth.joinTitle')}</h2>
              <p className="text-[15px] leading-relaxed text-[#E6EFF5]">{t('landing.ctaText')}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                to="/register"
                className="inline-flex min-h-[50px] items-center justify-center gap-2 rounded-xl bg-[#FFFEFA] px-6 text-base font-bold text-[#234A65] transition-colors hover:bg-[#EAF3F8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                {t('auth.requestAccount')}
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link
                to="/login"
                className="inline-flex min-h-[50px] items-center justify-center rounded-xl border border-[#9CC0D6] px-6 text-base font-bold text-white transition-colors hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                {t('auth.login')}
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-respira-border bg-respira-chrome">
        <p className={`${sectionWidth} py-5 text-[13px] leading-relaxed text-respira-muted`}>{t('landing.footer')}</p>
      </footer>
    </div>
  )
}
