import { Languages, MonitorCog, Moon, ShieldCheck, Sun } from 'lucide-react'
import type { ReactNode } from 'react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/common/PageHeader'
import { useI18n, type Language } from '../i18n/I18nContext'
import { getApiBaseUrl } from '../services/api'
import { useTheme, type Theme } from '../theme/ThemeContext'

interface Option<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

/** Selector de dos o más opciones excluyentes (idioma, tema), accesible como grupo de botones de radio. */
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
      className="mt-4 inline-flex rounded-xl border border-respira-border bg-respira-surface-alt p-1"
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

export function SettingsPage() {
  const { t, language, setLanguage } = useI18n()
  const { theme, setTheme } = useTheme()

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('settings.eyebrow')}
        title={t('settings.title')}
        icon={MonitorCog}
        description={t('settings.description')}
      />
      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
              <Languages aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="font-bold">{t('settings.language')}</h2>
              <p className="mt-1 text-sm leading-6 text-respira-muted">{t('settings.languageNote')}</p>
              <Segmented<Language>
                label={t('settings.language')}
                value={language}
                onChange={setLanguage}
                options={[
                  { value: 'es', label: 'Español' },
                  { value: 'en', label: 'English' },
                ]}
              />
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
              {theme === 'dark' ? <Moon aria-hidden="true" /> : <Sun aria-hidden="true" />}
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="font-bold">{t('settings.appearance')}</h2>
              <p className="mt-1 text-sm leading-6 text-respira-muted">{t('settings.appearanceNote')}</p>
              <Segmented<Theme>
                label={t('settings.appearance')}
                value={theme}
                onChange={setTheme}
                options={[
                  { value: 'light', label: t('settings.light'), icon: <Sun size={16} aria-hidden="true" /> },
                  { value: 'dark', label: t('settings.dark'), icon: <Moon size={16} aria-hidden="true" /> },
                ]}
              />
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sky-100 text-sky-800">
              <MonitorCog aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="font-bold">{t('settings.connection')}</h2>
              <p className="mt-1 text-sm text-respira-muted">{t('settings.connectionNote')}</p>
              <code className="mt-4 block break-all rounded-xl border border-respira-border bg-respira-surface-alt px-4 py-3 text-sm text-respira-body">
                {getApiBaseUrl()}
              </code>
            </div>
          </div>
        </Card>
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
              <ShieldCheck aria-hidden="true" />
            </span>
            <div>
              <h2 className="font-bold">{t('settings.scope')}</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-respira-muted">{t('settings.scopeNote')}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
