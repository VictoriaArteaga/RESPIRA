// @vitest-environment node
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  isSafeExternalUrl,
  isTrustedRendererUrl,
  parseSetActiveArgs,
  readCredentials,
  sanitizeApiResult,
} from './security'

const packaged = { fileUrl: 'file:///C:/Program%20Files/RESPIRA/resources/app/out/renderer/index.html' }
const dev = { devServerUrl: 'http://localhost:5173', fileUrl: packaged.fileUrl }

describe('isTrustedRendererUrl (senderFrame y navegación)', () => {
  it('acepta la interfaz empaquetada, incluso con hash o query', () => {
    expect(isTrustedRendererUrl(packaged.fileUrl, packaged)).toBe(true)
    expect(isTrustedRendererUrl(`${packaged.fileUrl}#/admin/users`, packaged)).toBe(true)
    expect(isTrustedRendererUrl(`${packaged.fileUrl}?x=1`, packaged)).toBe(true)
  })

  it('rechaza otros archivos locales, otros protocolos y URLs inválidas o ausentes', () => {
    expect(isTrustedRendererUrl('file:///C:/Users/otro/malicioso.html', packaged)).toBe(false)
    expect(isTrustedRendererUrl('https://example.com/', packaged)).toBe(false)
    expect(isTrustedRendererUrl('about:blank', packaged)).toBe(false)
    expect(isTrustedRendererUrl('javascript:alert(1)', packaged)).toBe(false)
    expect(isTrustedRendererUrl('no es una url', packaged)).toBe(false)
    expect(isTrustedRendererUrl('', packaged)).toBe(false)
    expect(isTrustedRendererUrl(undefined, packaged)).toBe(false)
  })

  it('en desarrollo solo confía en el origen del servidor de Vite', () => {
    expect(isTrustedRendererUrl('http://localhost:5173/#/dashboard', dev)).toBe(true)
    expect(isTrustedRendererUrl('http://localhost:5174/', dev)).toBe(false)
    expect(isTrustedRendererUrl('http://localhost.evil.com:5173/', dev)).toBe(false)
    expect(isTrustedRendererUrl(packaged.fileUrl, dev)).toBe(false)
  })
})

describe('isSafeExternalUrl', () => {
  it('solo permite enlaces http(s)', () => {
    expect(isSafeExternalUrl('https://leafletjs.com')).toBe(true)
    expect(isSafeExternalUrl('http://example.com')).toBe(true)
    for (const url of ['file:///C:/Windows/System32/calc.exe', 'javascript:alert(1)', 'ms-msdt:/x', 'smb://host/x', 'basura']) {
      expect(isSafeExternalUrl(url)).toBe(false)
    }
  })
})

describe('sanitizeApiResult (errores hacia el renderer)', () => {
  it('reemplaza el cuerpo de los errores 5xx por un mensaje controlado', () => {
    const result = sanitizeApiResult({ status: 500, body: { detail: 'Traceback: password authentication failed for user' } })

    expect(result).toEqual({ status: 500, body: { detail: 'El servidor no pudo completar la solicitud.' } })
    expect(JSON.stringify(result)).not.toContain('Traceback')
  })

  it('no refleja la entrada en los errores de validación 422', () => {
    const result = sanitizeApiResult({ status: 422, body: { detail: [{ input: 'Mi-contrasena-1234', msg: 'x' }] } })

    expect(JSON.stringify(result)).not.toContain('Mi-contrasena')
  })

  it('deja pasar respuestas correctas y errores de cliente comunes', () => {
    expect(sanitizeApiResult({ status: 200, body: [1] })).toEqual({ status: 200, body: [1] })
    expect(sanitizeApiResult({ status: 401, body: { detail: 'no' } })).toEqual({ status: 401, body: { detail: 'no' } })
    expect(sanitizeApiResult({ status: 0, body: { detail: 'sin red' } }).status).toBe(0)
  })
})

describe('parseSetActiveArgs (canal admin-users-set-active)', () => {
  it('acepta un id entero positivo y un booleano', () => {
    expect(parseSetActiveArgs(7, true)).toEqual({ userId: 7, isActive: true })
    expect(parseSetActiveArgs(1, false)).toEqual({ userId: 1, isActive: false })
  })

  it('rechaza ids no válidos y valores no booleanos', () => {
    for (const id of [0, -1, 1.5, NaN, Infinity, 2 ** 60, '1', null, undefined, {}, [1]]) {
      expect(parseSetActiveArgs(id, true)).toBeNull()
    }
    for (const flag of ['true', 1, 0, null, undefined, {}]) {
      expect(parseSetActiveArgs(1, flag)).toBeNull()
    }
  })

  it('el resultado nunca incluye rol ni campos adicionales', () => {
    expect(Object.keys(parseSetActiveArgs(1, true) ?? {}).sort()).toEqual(['isActive', 'userId'])
  })
})

describe('readCredentials', () => {
  it('valida tipo y longitud', () => {
    expect(readCredentials({ email: 'a@b.co', password: 'x' })).toEqual({ email: 'a@b.co', password: 'x' })
    expect(readCredentials({ email: '', password: 'x' })).toBeNull()
    expect(readCredentials({ email: 'a@b.co', password: 'x'.repeat(129) })).toBeNull()
    expect(readCredentials({ email: 'a'.repeat(255), password: 'x' })).toBeNull()
    expect(readCredentials({ email: 1, password: 'x' })).toBeNull()
    expect(readCredentials(null)).toBeNull()
    expect(readCredentials('texto')).toBeNull()
  })

  it('descarta campos adicionales enviados por el renderer (p. ej. un token)', () => {
    const parsed = readCredentials({ email: 'a@b.co', password: 'x', token: 'robado', role: 'admin' })

    expect(parsed).toEqual({ email: 'a@b.co', password: 'x' })
  })
})

describe('superficie expuesta por el preload', () => {
  const preload = readFileSync(resolve(__dirname, 'preload.ts'), 'utf-8')

  it('no maneja tokens ni cabeceras de autorización', () => {
    expect(preload).not.toMatch(/token|authorization|bearer/i)
  })

  it('las funciones admin solo reciben el id y el estado', () => {
    expect(preload).toMatch(/setUserActive: \(userId: number, isActive: boolean\)/)
    expect(preload).not.toMatch(/role/i)
  })
})

describe('proceso principal (main.ts)', () => {
  const main = readFileSync(resolve(__dirname, 'main.ts'), 'utf-8')

  it('todos los canales IPC pasan por secureHandle (validación de senderFrame)', () => {
    expect(main.match(/ipcMain\.handle\(/g)).toHaveLength(1) // solo dentro de secureHandle
    expect(main.match(/secureHandle\('respira:/g)).toHaveLength(7)
  })

  it('el token solo se asigna tras un inicio de sesión correcto y se lee de la respuesta del servidor', () => {
    const assignments = main.match(/^\s*accessToken = .*$/gm) ?? []

    expect(assignments.map((line) => line.trim())).toEqual([
      'accessToken = null',
      'accessToken = safeStorage.decryptString(readFileSync(sessionFile()))',
      'accessToken = token',
    ])
  })

  it('bloquea navegaciones no autorizadas', () => {
    expect(main).toContain("window.webContents.on('will-navigate'")
    expect(main).toContain("window.webContents.on('will-redirect'")
  })

  it('el PATCH administrativo solo envía is_active', () => {
    expect(main.match(/apiRequest\('PATCH'/g)).toHaveLength(1)
    expect(main).toContain('{ is_active: args.isActive }')
  })
})
