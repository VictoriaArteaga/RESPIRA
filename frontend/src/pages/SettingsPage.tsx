import {
  AppWindow,
  Eye,
  Home,
  Languages,
  MonitorCog,
  Moon,
  RotateCcw,
  ShieldCheck,
  Sun,
  type LucideIcon,
} from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../context/AuthContext'
import { useI18n, type Language } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import {
  START_PAGES,
  usePreferences,
  type Density,
  type StartPage,
  type TextSize,
} from '../preferences/PreferencesContext'
import { useTheme, type Theme } from '../theme/ThemeContext'

interface Option<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

/** Selector de dos o más opciones excluyentes (idioma, tema…), accesible como grupo de botones de radio. */
function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: T
  options: Option<T>[]
  onChange: (value: T) => void
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="inline-flex flex-wrap rounded-xl border border-respira-border bg-respira-surface-alt p-1"
    >
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(option.value)}
            className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-4 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-respira-blue-dark ${
              active ? 'bg-respira-blue text-white shadow-sm' : 'text-respira-body hover:bg-sky-100'
            }`}
          >
            {option.icon}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

function SettingCard({
  icon: Icon,
  tone = 'sky',
  title,
  note,
  className = '',
  children,
}: {
  icon: LucideIcon
  tone?: 'sky' | 'amber' | 'emerald'
  title: string
  note?: string
  className?: string
  children?: ReactNode
}) {
  const tones = {
    sky: 'bg-sky-100 text-sky-800',
    amber: 'bg-amber-100 text-amber-800',
    emerald: 'bg-emerald-100 text-emerald-800',
  }
  return (
    <Card className={`p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${tones[tone]}`}>
          <Icon aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="font-bold">{title}</h2>
          {note && <p className="mt-1 max-w-3xl text-sm leading-6 text-respira-muted">{note}</p>}
          {children && <div className="mt-4">{children}</div>}
        </div>
      </div>
    </Card>
  )
}

const START_LABELS: Record<StartPage, TranslationKey> = {
  '/dashboard': 'nav.dashboard',
  '/municipalities': 'nav.municipalities',
  '/risk-map': 'nav.riskMap',
  '/endemic': 'nav.endemic',
  '/cases': 'nav.cases',
  '/alerts': 'nav.alerts',
}

export function SettingsPage() {
  const { t, language, setLanguage } = useI18n()
  const { theme, setTheme } = useTheme()
  const preferences = usePreferences()
  const { user } = useAuth()
  const [resetDone, setResetDone] = useState(false)

  const resetAll = () => {
    preferences.reset()
    setTheme('light')
    setLanguage('es')
    setResetDone(true)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('settings.eyebrow')}
        title={t('settings.title')}
        icon={MonitorCog}
        description={t('settings.description')}
      />
      <div className="grid gap-5 lg:grid-cols-2">
        <SettingCard icon={Languages} title={t('settings.language')} note={t('settings.languageNote')}>
          <Segmented<Language>
            label={t('settings.language')}
            value={language}
            onChange={setLanguage}
            options={[
              { value: 'es', label: 'Español' },
              { value: 'en', label: 'English' },
            ]}
          />
        </SettingCard>

        <SettingCard
          icon={theme === 'dark' ? Moon : Sun}
          tone="amber"
          title={t('settings.appearance')}
          note={t('settings.appearanceNote')}
        >
          <Segmented<Theme>
            label={t('settings.appearance')}
            value={theme}
            onChange={setTheme}
            options={[
              { value: 'light', label: t('settings.light'), icon: <Sun size={16} aria-hidden="true" /> },
              { value: 'dark', label: t('settings.dark'), icon: <Moon size={16} aria-hidden="true" /> },
            ]}
          />
        </SettingCard>

        <SettingCard
          className="lg:col-span-2"
          icon={Eye}
          title={t('settings.reading')}
          note={t('settings.readingNote')}
        >
          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <p className="mb-2 text-xs font-semibold">{t('settings.textSize')}</p>
              <Segmented<TextSize>
                label={t('settings.textSize')}
                value={preferences.textSize}
                onChange={(value) => preferences.setPreference('textSize', value)}
                options={[
                  { value: 'normal', label: t('settings.textNormal') },
                  { value: 'large', label: t('settings.textLarge') },
                ]}
              />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold">{t('settings.density')}</p>
              <Segmented<Density>
                label={t('settings.density')}
                value={preferences.density}
                onChange={(value) => preferences.setPreference('density', value)}
                options={[
                  { value: 'comfortable', label: t('settings.comfortable') },
                  { value: 'compact', label: t('settings.compact') },
                ]}
              />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold">{t('settings.motion')}</p>
              <Segmented<'full' | 'reduced'>
                label={t('settings.motion')}
                value={preferences.reduceMotion ? 'reduced' : 'full'}
                onChange={(value) => preferences.setPreference('reduceMotion', value === 'reduced')}
                options={[
                  { value: 'full', label: t('settings.motionFull') },
                  { value: 'reduced', label: t('settings.motionReduced') },
                ]}
              />
            </div>
          </div>
        </SettingCard>

        <SettingCard icon={Home} tone="emerald" title={t('settings.start')} note={t('settings.startNote')}>
          <label className="grid max-w-xs gap-1.5 text-xs font-semibold">
            {t('settings.startLabel')}
            <select
              className="field-control"
              value={preferences.startPage}
              onChange={(event) => preferences.setPreference('startPage', event.target.value as StartPage)}
            >
              {START_PAGES.map((path) => (
                <option key={path} value={path}>
                  {t(START_LABELS[path])}
                </option>
              ))}
            </select>
          </label>
        </SettingCard>

        <SettingCard icon={AppWindow} title={t('settings.app')} note={t('settings.appNote')}>
          <dl className="divide-y divide-respira-border text-sm">
            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-respira-muted">{t('settings.platform')}</dt>
              <dd className="font-semibold">
                {window.respiraDesktop ? t('settings.platformDesktop') : t('settings.platformWeb')}
              </dd>
            </div>
            {user && (
              <>
                <div className="flex justify-between gap-4 py-2.5">
                  <dt className="text-respira-muted">{t('settings.signedAs')}</dt>
                  <dd className="min-w-0 truncate font-semibold" title={user.email}>
                    {user.email}
                  </dd>
                </div>
                <div className="flex justify-between gap-4 py-2.5">
                  <dt className="text-respira-muted">{t('settings.role')}</dt>
                  <dd className="font-semibold">
                    {user.role === 'admin' ? t('admin.roleAdmin') : t('admin.roleAnalyst')}
                  </dd>
                </div>
              </>
            )}
          </dl>
        </SettingCard>

        <SettingCard
          className="lg:col-span-2"
          icon={ShieldCheck}
          tone="amber"
          title={t('settings.scope')}
          note={t('settings.scopeNote')}
        />

        <Card className="p-6 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-800">
                <RotateCcw aria-hidden="true" />
              </span>
              <div>
                <h2 className="font-bold">{t('settings.reset')}</h2>
                <p className="mt-1 text-sm leading-6 text-respira-muted">{t('settings.resetNote')}</p>
                {resetDone && (
                  <p className="mt-2 text-sm font-semibold text-emerald-800" role="status">
                    {t('settings.resetDone')}
                  </p>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={resetAll}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-respira-border bg-respira-surface px-5 text-sm font-semibold text-respira-text transition-colors hover:bg-sky-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-respira-blue-dark"
            >
              <RotateCcw size={16} aria-hidden="true" />
              {t('settings.resetButton')}
            </button>
          </div>
        </Card>
      </div>
    </div>
  )
}
