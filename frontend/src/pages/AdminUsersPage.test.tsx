import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { ApiError } from '../services/api'
import * as adminService from '../services/adminService'
import * as authService from '../services/authService'
import { adminUser, analystUser, disabledUser, pendingUser } from '../test/fixtures'
import { AdminUsersPage } from './AdminUsersPage'

vi.mock('../services/adminService')
vi.mock('../services/authService')

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <AdminUsersPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

const allUsers = [adminUser, analystUser, pendingUser, disabledUser]

beforeEach(() => {
  vi.mocked(authService.restoreSession).mockResolvedValue(adminUser)
  vi.mocked(adminService.listUsers).mockResolvedValue(allUsers)
  vi.mocked(adminService.setUserActive).mockResolvedValue(pendingUser)
})

describe('AdminUsersPage', () => {
  it('muestra el listado con correo, rol, estado en texto y fecha', async () => {
    renderPage()

    const row = (await screen.findByText('pendiente@example.com')).closest('tr') as HTMLElement
    expect(within(row).getByText('Analista')).toBeInTheDocument()
    expect(within(row).getByText('Pendiente de aprobación')).toBeInTheDocument()
    expect(within(row).getByText(new Date(pendingUser.created_at).toLocaleDateString('es-CO'))).toBeInTheDocument()
    expect(screen.getByText('Desactivada')).toBeInTheDocument()
    expect(screen.getAllByText('Activa')).toHaveLength(2)
    expect(screen.getByText('Administrador')).toBeInTheDocument()
  })

  it('muestra el indicador de carga mientras consulta', () => {
    vi.mocked(adminService.listUsers).mockReturnValue(new Promise(() => {}))

    renderPage()

    expect(screen.getByRole('status')).toHaveTextContent('Cargando usuarios')
  })

  it('muestra un estado vacío cuando no hay usuarios', async () => {
    vi.mocked(adminService.listUsers).mockResolvedValue([])

    renderPage()

    expect(await screen.findByText('No hay usuarios registrados.')).toBeInTheDocument()
  })

  it('muestra el error de consulta sin romper la interfaz y permite reintentar', async () => {
    vi.mocked(adminService.listUsers).mockRejectedValueOnce(new ApiError('No fue posible conectar con el servidor.', 0))

    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible conectar con el servidor.')
    await userEvent.click(screen.getByRole('button', { name: 'Actualizar' }))
    expect(await screen.findByText('analista@example.com')).toBeInTheDocument()
  })

  it('aprobar llama al servicio correcto, confirma y recarga el listado', async () => {
    vi.mocked(adminService.listUsers)
      .mockResolvedValueOnce(allUsers)
      .mockResolvedValueOnce([adminUser, analystUser, { ...pendingUser, is_active: true, status: 'active' }, disabledUser])

    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Aprobar cuenta de pendiente@example.com' }))

    expect(adminService.setUserActive).toHaveBeenCalledWith(pendingUser.id, true)
    expect(await screen.findByText('Se aprobó la cuenta de pendiente@example.com.')).toBeInTheDocument()
    await waitFor(() => expect(adminService.listUsers).toHaveBeenCalledTimes(2))
    expect(screen.queryByRole('button', { name: /Aprobar cuenta/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Desactivar cuenta de pendiente@example.com' })).toBeInTheDocument()
  })

  it('reactivar una cuenta desactivada usa is_active=true', async () => {
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: 'Reactivar cuenta de desactivada@example.com' }))

    expect(adminService.setUserActive).toHaveBeenCalledWith(disabledUser.id, true)
    expect(await screen.findByText('Se reactivó la cuenta de desactivada@example.com.')).toBeInTheDocument()
  })

  it('desactivar exige confirmación y se puede cancelar', async () => {
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar cuenta de analista@example.com' }))
    const dialog = screen.getByRole('alertdialog')
    expect(dialog).toHaveTextContent('analista@example.com')
    expect(adminService.setUserActive).not.toHaveBeenCalled()

    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(adminService.setUserActive).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Desactivar cuenta de analista@example.com' }))
    await userEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Desactivar cuenta' }))

    expect(adminService.setUserActive).toHaveBeenCalledWith(analystUser.id, false)
    expect(await screen.findByText('Se desactivó la cuenta de analista@example.com.')).toBeInTheDocument()
    await waitFor(() => expect(adminService.listUsers).toHaveBeenCalledTimes(2))
  })

  it('durante la acción muestra carga, deshabilita las acciones y evita solicitudes duplicadas', async () => {
    let finish: (user: typeof pendingUser) => void = () => {}
    vi.mocked(adminService.setUserActive).mockReturnValue(new Promise((resolve) => (finish = resolve)))

    renderPage()
    const approve = await screen.findByRole('button', { name: 'Aprobar cuenta de pendiente@example.com' })
    await userEvent.click(approve)
    await userEvent.click(approve)

    expect(adminService.setUserActive).toHaveBeenCalledTimes(1)
    expect(approve).toBeDisabled()
    expect(approve).toHaveTextContent('Procesando...')
    expect(screen.getByRole('button', { name: 'Desactivar cuenta de analista@example.com' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Actualizar' })).toBeDisabled()

    finish(pendingUser)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Actualizar' })).toBeEnabled())
  })

  it('muestra el error de una acción fallida sin revelar detalles internos', async () => {
    vi.mocked(adminService.setUserActive).mockRejectedValue(new ApiError('No fue posible completar la operación.', 500))

    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Aprobar cuenta de pendiente@example.com' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible completar la operación.')
    expect(screen.getByText('pendiente@example.com')).toBeInTheDocument()
  })

  it('no ofrece acciones sobre la cuenta del administrador autenticado', async () => {
    renderPage()

    const row = (await screen.findByText('admin@example.com')).closest('tr') as HTMLElement
    expect(within(row).getByText('Tu cuenta')).toBeInTheDocument()
    expect(within(row).queryByRole('button')).not.toBeInTheDocument()
  })

  it('no ofrece cambiar roles ni eliminar cuentas', async () => {
    renderPage()

    await screen.findByText('analista@example.com')
    expect(screen.queryByRole('button', { name: /rol|eliminar|borrar/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})
