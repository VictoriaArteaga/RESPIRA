import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button } from '../components/common/Button'
import { Card } from '../components/common/Card'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../services/api'

type Mode = 'login' | 'register'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Misma política que el servidor (12–128 caracteres, al menos una letra y un número); el servidor valida de nuevo.
function validate(mode: Mode, email: string, password: string, confirmation: string): string | null {
  if (!EMAIL_PATTERN.test(email.trim())) return 'Ingresa un correo electrónico válido.'
  if (mode === 'login') return password ? null : 'Ingresa tu contraseña.'
  if (password.length < 12 || password.length > 128) return 'La contraseña debe tener entre 12 y 128 caracteres.'
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return 'La contraseña debe incluir al menos una letra y un número.'
  if (password !== confirmation) return 'Las contraseñas no coinciden.'
  return null
}

export function AuthPage({ mode }: { mode: Mode }) {
  const { status, login, register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated') return <Navigate to="/dashboard" replace />

  const isLogin = mode === 'login'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setNotice(null)
    const problem = validate(mode, email, password, confirmation)
    if (problem) {
      setError(problem)
      return
    }

    setError(null)
    setSubmitting(true)
    try {
      if (isLogin) {
        await login({ email: email.trim(), password })
        navigate('/dashboard', { replace: true })
      } else {
        await register({ email: email.trim(), password })
        setNotice('Solicitud enviada. Un administrador debe aprobar tu cuenta antes de que puedas iniciar sesión.')
        setPassword('')
        setConfirmation('')
        navigate('/login', { replace: true })
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Ocurrió un error inesperado.')
    } finally {
      setSubmitting(false)
      setPassword('')
    }
  }

  const inputClass =
    'mt-1 w-full rounded-xl border border-respira-border bg-white px-3 py-2.5 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-respira-blue-dark'

  return (
    <div className="app-shell flex min-h-screen items-center justify-center p-5 text-respira-text">
      <Card className="w-full max-w-md p-8">
        <p className="text-sm font-semibold text-sky-800">RESPIRA</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">{isLogin ? 'Iniciar sesión' : 'Crear cuenta'}</h1>
        <p className="mt-2 text-sm text-respira-muted">
          Monitoreo epidemiológico de infecciones respiratorias agudas en Nariño.
        </p>

        <form className="mt-6 space-y-4" onSubmit={(event) => void handleSubmit(event)} noValidate>
          <label className="block text-sm font-medium">
            Correo electrónico
            <input
              className={inputClass}
              type="email"
              autoComplete="email"
              maxLength={254}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium">
            Contraseña
            <input
              className={inputClass}
              type="password"
              autoComplete={isLogin ? 'current-password' : 'new-password'}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {!isLogin && (
            <label className="block text-sm font-medium">
              Confirmar contraseña
              <input
                className={inputClass}
                type="password"
                autoComplete="new-password"
                maxLength={128}
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                required
              />
              <span className="mt-1 block text-xs font-normal text-respira-muted">
                Mínimo 12 caracteres, con al menos una letra y un número.
              </span>
            </label>
          )}

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

          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? 'Procesando...' : isLogin ? 'Iniciar sesión' : 'Solicitar cuenta'}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-respira-muted">
          {isLogin ? '¿No tienes cuenta? ' : '¿Ya tienes cuenta? '}
          <Link className="font-semibold text-respira-blue hover:underline" to={isLogin ? '/register' : '/login'}>
            {isLogin ? 'Regístrate' : 'Inicia sesión'}
          </Link>
        </p>
      </Card>
    </div>
  )
}
