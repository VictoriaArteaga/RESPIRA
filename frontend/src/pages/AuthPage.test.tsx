import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { PreferencesProvider } from '../preferences/PreferencesContext'
import * as authService from '../services/authService'
import { AuthPage } from './AuthPage'

vi.mock('../services/authService')

async function renderAuth(mode: 'login' | 'register') {
  vi.mocked(authService.restoreSession).mockResolvedValue(null)
  render(
    <MemoryRouter>
      <AuthProvider>
        <PreferencesProvider>
          <AuthPage mode={mode} />
        </PreferencesProvider>
      </AuthProvider>
    </MemoryRouter>,
  )
  await screen.findByRole('button', { name: /Iniciar sesión|Solicitar/i })
}

const limitMessage = /Llegaste al límite: ya no caben más letras, números ni signos \(máximo (\d+)\)/

describe('formularios de acceso: aviso al llegar al máximo de caracteres', () => {
  it('inicio de sesión: la contraseña se pone en roja y avisa solo al llegar a 64', async () => {
    await renderAuth('login')
    const password = screen.getByLabelText('Contraseña')

    fireEvent.change(password, { target: { value: 'a'.repeat(63) } })
    expect(screen.queryByText(limitMessage)).not.toBeInTheDocument()
    expect(password).toHaveAttribute('aria-invalid', 'false')

    fireEvent.change(password, { target: { value: 'a'.repeat(64) } })
    expect(screen.getByText(limitMessage)).toHaveTextContent('máximo 64')
    expect(password).toHaveAttribute('aria-invalid', 'true')
    expect(password).toHaveAttribute('aria-describedby', 'password-limit')
    expect(password.parentElement).toHaveClass('border-rose-500')
  })

  it('inicio de sesión: el correo avisa al llegar a 254', async () => {
    await renderAuth('login')
    const email = screen.getByLabelText('Correo electrónico')

    fireEvent.change(email, { target: { value: 'a'.repeat(254) } })

    expect(screen.getByText(limitMessage)).toHaveTextContent('máximo 254')
    expect(email.parentElement).toHaveClass('border-rose-500')
  })

  it('registro: cada campo avisa por separado y el aviso se quita al borrar', async () => {
    await renderAuth('register')
    const password = screen.getByLabelText('Contraseña')
    const confirmation = screen.getByLabelText('Confirmar contraseña')

    fireEvent.change(password, { target: { value: 'b'.repeat(64) } })
    expect(screen.getAllByText(limitMessage)).toHaveLength(1)
    expect(confirmation.parentElement).not.toHaveClass('border-rose-500')

    fireEvent.change(confirmation, { target: { value: 'b'.repeat(64) } })
    expect(screen.getAllByText(limitMessage)).toHaveLength(2)

    fireEvent.change(password, { target: { value: 'b'.repeat(10) } })
    expect(screen.getAllByText(limitMessage)).toHaveLength(1)
    expect(password.parentElement).not.toHaveClass('border-rose-500')
  })
})
