import { useState, type FormEvent } from 'react'
import { Activity, Eye, EyeOff, Lock, Mail, UserPlus } from 'lucide-react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../components/common/Button'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../i18n/I18nContext'
import type { TranslationKey } from '../i18n/translations'
import { ApiError } from '../services/api'

type Mode = 'login' | 'register'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

type Field = 'email' | 'password' | 'confirmation'
interface Problem {
  field: Field
  message: TranslationKey
}

// Misma política que el servidor (12–128 caracteres, al menos una letra y un número); el servidor valida de nuevo.
function validate(mode: Mode, email: string, password: string, confirmation: string): Problem | null {
  if (!email.trim()) return { field: 'email', message: 'auth.errEmailEmpty' }
  if (!EMAIL_PATTERN.test(email.trim())) return { field: 'email', message: 'auth.errEmailInvalid' }
  if (!password) return { field: 'password', message: 'auth.errPasswordEmpty' }
  if (mode === 'login') return null
  if (!confirmation) return { field: 'confirmation', message: 'auth.errConfirmEmpty' }
  if (password.length < 12 || password.length > 128) return { field: 'password', message: 'auth.errPasswordLength' }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password))
    return { field: 'password', message: 'auth.errPasswordFormat' }
  if (password !== confirmation) return { field: 'confirmation', message: 'auth.errMismatch' }
  return null
}

const fieldClass =
  'flex h-12 items-center gap-2.5 rounded-xl border border-respira-field-border bg-respira-field pl-3.5 text-respira-body focus-within:border-respira-blue-dark focus-within:outline focus-within:outline-2 focus-within:outline-respira-blue-dark'
const inputClass =
  'h-full min-w-0 flex-1 bg-transparent text-sm text-respira-text outline-none placeholder:text-respira-muted'
const helpClass = 'text-xs text-respira-body'

export function AuthPage({ mode }: { mode: Mode }) {
  const { status, login, register } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [invalidField, setInvalidField] = useState<Field | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated') return <Navigate to="/" replace />

  const isLogin = mode === 'login'
  const passwordType = showPassword ? 'text' : 'password'
  const EyeIcon = showPassword ? EyeOff : Eye

  const fieldClassFor = (field: Field, padding: string) =>
    `${fieldClass} ${padding} ${invalidField === field ? 'border-rose-500 bg-rose-50/60' : ''}`

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setNotice(null)
    const problem = validate(mode, email, password, confirmation)
    if (problem) {
      setError(t(problem.message))
      setInvalidField(problem.field)
      return
    }

    setError(null)
    setInvalidField(null)
    setSubmitting(true)
    try {
      if (isLogin) {
        await login({ email: email.trim(), password })
        navigate('/', { replace: true })
      } else {
        await register({ email: email.trim(), password })
        setNotice(t('auth.requestSent'))
        setPassword('')
        setConfirmation('')
        navigate('/login', { replace: true })
      }
    } catch (caught) {
      setInvalidField(null)
      setError(caught instanceof ApiError ? caught.message : t('common.unexpected'))
    } finally {
      setSubmitting(false)
      setPassword('')
    }
  }

  const visibilityToggle = (
    <button
      type="button"
      onClick={() => setShowPassword((current) => !current)}
      aria-label={showPassword ? t('auth.hidePassword') : t('auth.showPassword')}
      className="flex h-11 w-11 flex-none items-center justify-center rounded-[10px] text-respira-body hover:text-respira-blue-dark"
    >
      <EyeIcon size={20} aria-hidden="true" />
    </button>
  )

  const feedback = (
    <>
      {error && (
        <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800" role="status">
          {notice}
        </p>
      )}
    </>
  )

  const submitClass = 'mt-1.5 h-[50px] w-full rounded-xl text-base font-bold shadow-[0_4px_14px_rgba(49,95,125,0.25)]'

  if (isLogin) {
    return (
      <div className="auth-shell flex min-h-screen items-center justify-center px-5 py-8 text-respira-text">
        <main className="auth-scale w-full max-w-md overflow-hidden rounded-[20px] border border-respira-border bg-respira-surface shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
          <div className="h-[5px] bg-gradient-to-r from-respira-blue to-[#6F9BB5]" />
          <div className="flex flex-col items-center px-10 pb-9 pt-9">
            <div
              role="img"
              aria-label={t('auth.logoAlt')}
              className="flex h-[68px] w-[68px] items-center justify-center rounded-[20px] bg-respira-blue text-[34px] font-black text-white shadow-[0_6px_16px_rgba(49,95,125,0.25)]"
            >
              R
            </div>
            <p className="mt-[18px] text-[13px] font-bold tracking-[0.16em] text-respira-link">RESPIRA</p>
            <h1 className="mt-1.5 text-[30px] font-extrabold tracking-tight">{t('auth.welcome')}</h1>
            <p className="mt-2 text-center text-sm leading-6 text-respira-body">{t('auth.loginIntro')}</p>

            <form
              className="mt-7 flex w-full flex-col gap-[18px]"
              onSubmit={(event) => void handleSubmit(event)}
              noValidate
            >
              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-sm font-semibold">
                  {t('auth.email')}
                </label>
                <div className={fieldClassFor('email', 'pr-3.5')}>
                  <Mail size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="email"

                    aria-invalid={invalidField === 'email'}
                    className={inputClass}
                    type="email"
                    autoComplete="email"
                    maxLength={254}
                    placeholder={t('auth.emailPlaceholder')}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="password" className="text-sm font-semibold">
                  {t('auth.password')}
                </label>
                <div className={fieldClassFor('password', 'pr-1.5')}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="password"

                    aria-invalid={invalidField === 'password'}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="current-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
              </div>

              {feedback}

              <Button className={submitClass} type="submit" disabled={submitting}>
                {submitting ? t('common.processing') : t('auth.login')}
              </Button>
            </form>

            <p className="mt-[22px] text-center text-sm text-respira-body">
              {t('auth.noAccount')}{' '}
              <Link className="font-bold text-respira-link hover:text-respira-blue-dark" to="/register">
                {t('auth.registerLink')}
              </Link>
            </p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="auth-shell flex min-h-screen items-center justify-center px-5 py-8 text-respira-text">
      <main className="auth-scale flex w-full max-w-[960px] flex-wrap overflow-hidden rounded-[20px] border border-respira-border bg-respira-surface shadow-[0_12px_36px_rgba(36,59,74,0.10)]">
        <aside className="flex min-w-0 flex-[1_1_340px] flex-col justify-between gap-5 bg-gradient-to-br from-[#315F7D] to-[#234A65] px-10 py-12 text-white">
          <div className="flex flex-col gap-5">
            <UserPlus size={40} aria-hidden="true" />
            <h2 className="text-[28px] font-extrabold leading-tight tracking-tight">{t('auth.joinTitle')}</h2>
            <p className="hyphens-auto text-justify text-[15px] leading-relaxed text-[#E6EFF5]">{t('auth.joinText')}</p>
          </div>
          <div className="flex items-center gap-2.5 text-sm font-semibold">
            <Activity size={20} aria-hidden="true" className="flex-none" />
            <span>{t('layout.tagline')}</span>
          </div>
        </aside>

        <section className="flex min-w-0 flex-[999_1_420px] flex-col px-12 pb-10 pt-12">
          <h1 className="text-[30px] font-extrabold tracking-tight">{t('auth.createTitle')}</h1>
          <p className="mt-2 text-sm text-respira-body">{t('auth.createIntro')}</p>

          <form className="mt-7 flex flex-col gap-[18px]" onSubmit={(event) => void handleSubmit(event)} noValidate>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-sm font-semibold">
                {t('auth.email')}
              </label>
              <div className={fieldClassFor('email', 'pr-3.5')}>
                <Mail size={19} aria-hidden="true" className="flex-none" />
                <input
                  id="email"

                  aria-invalid={invalidField === 'email'}
                  className={inputClass}
                  type="email"
                  autoComplete="email"
                  maxLength={254}
                  placeholder={t('auth.emailPlaceholder')}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <span className={helpClass}>{t('auth.emailHelp')}</span>
            </div>

            <div className="flex flex-wrap gap-[18px]">
              <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-1.5">
                <label htmlFor="password" className="text-sm font-semibold">
                  {t('auth.password')}
                </label>
                <div className={fieldClassFor('password', 'pr-1.5')}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="password"

                    aria-invalid={invalidField === 'password'}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="new-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
                <span className={helpClass}>{t('auth.passwordHelp')}</span>
              </div>

              <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-1.5">
                <label htmlFor="confirmation" className="text-sm font-semibold">
                  {t('auth.confirmPassword')}
                </label>
                <div className={fieldClassFor('confirmation', 'pr-1.5')}>
                  <Lock size={19} aria-hidden="true" className="flex-none" />
                  <input
                    id="confirmation"

                    aria-invalid={invalidField === 'confirmation'}
                    className={inputClass}
                    type={passwordType}
                    autoComplete="new-password"
                    maxLength={128}
                    placeholder="••••••••••••"
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.target.value)}
                    required
                  />
                  {visibilityToggle}
                </div>
                <span className={helpClass}>{t('auth.confirmHelp')}</span>
              </div>
            </div>

            {feedback}

            <Button className={submitClass} type="submit" disabled={submitting}>
              {submitting ? t('common.processing') : t('auth.requestAccount')}
            </Button>
          </form>

          <p className="mt-[22px] text-center text-sm text-respira-body">
            {t('auth.haveAccount')}{' '}
            <Link className="font-bold text-respira-link hover:text-respira-blue-dark" to="/login">
              {t('auth.loginLink')}
            </Link>
          </p>
        </section>
      </main>
    </div>
  )
}
