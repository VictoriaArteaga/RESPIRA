# RESPIRA — Frontend

Aplicación de escritorio académica para apoyar el monitoreo de infecciones respiratorias agudas en menores de cinco años en Nariño. Incluye el dashboard inicial y la consulta básica de municipios y registros de casos.

> **Datos de desarrollo:** La API conectada entrega datos sintéticos de prueba. La interfaz los identifica como sintéticos y no los presenta como registros de SIVIGILA.

## Tecnologías

React, TypeScript, Vite, Electron, Tailwind CSS, React Router, Lucide React y Recharts.

## Requisitos

- Node.js 20 o posterior y npm.
- Backend RESPIRA ejecutándose en `http://localhost:8000` (o URL configurada).

## Instalación y configuración

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

`VITE_API_URL` indica la URL base del backend. Su valor predeterminado es `http://localhost:8000`.

## Desarrollo

Inicia Vite y Electron en modo desarrollo:

```powershell
npm run dev
```

## Verificación y empaquetado

```powershell
npm run typecheck
npm run build
npm run dist:win
npm run dist:linux
```

Los comandos `dist:*` preparan instaladores con electron-builder para Windows (NSIS) y Linux (AppImage). El empaquetado de cada plataforma debe ejecutarse en un sistema compatible.

## Rutas

- `/dashboard`: resumen, indicadores y tendencia semanal histórica.
- `/municipalities`: municipios, casos acumulados y última semana registrada.
- `/cases`: tabla de registros de casos.
- `/alerts`: placeholder informativo de una etapa posterior.
- `/settings`: URL configurada del backend y etiqueta del entorno.

La aplicación consume `/api/dashboard`, `/api/municipalities` y `/api/cases`. La configuración HTTP está centralizada en `src/services/api.ts`. La navegación usa rutas hash para funcionar correctamente al cargar la aplicación empaquetada desde archivos locales de Electron. En la aplicación de escritorio, las consultas GET pasan por un puente IPC limitado a los endpoints de lectura utilizados por esta interfaz, de modo que no requieren relajar CORS en la API.
