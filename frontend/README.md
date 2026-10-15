# RESPIRA — Frontend

Aplicación de escritorio académica para apoyar el monitoreo de infecciones respiratorias agudas en menores de cinco años en Nariño. Incluye el dashboard, consulta de municipios y casos, mapa estadístico de riesgo y canal endémico.

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

- `/dashboard`: resumen, indicadores, última semana disponible, recuento de alertas y tendencia semanal histórica.
- `/municipalities`: municipios, casos acumulados y última semana registrada. Cada fila abre un detalle con historial semanal, riesgo del periodo más reciente, canal endémico y variables sintéticas disponibles.
- `/cases`: tabla de registros de casos con filtros por año, semana epidemiológica y municipio.
- `/risk-map`: mapa de marcadores municipales, nivel estadístico de riesgo y filtros por año y semana.
- `/endemic`: canal endémico por municipio y año con percentiles históricos y estadísticas descriptivas.
- `/alerts`: listado filtrable de alertas estadísticas moderadas y altas, con periodo, valores observados, referencia histórica y explicación de la regla.
- `/settings`: URL configurada del backend y etiqueta del entorno.

La aplicación consume `/api/dashboard`, `/api/municipalities`, `/api/cases`, `/api/risk-map` y los endpoints municipales de riesgo y canal endémico. Leaflet usa mosaicos de OpenStreetMap con conexión a internet. Los datos siguen siendo sintéticos; no hay IA ni predicción futura. La configuración HTTP está centralizada en `src/services/api.ts`. La navegación usa rutas hash para funcionar correctamente al cargar la aplicación empaquetada desde archivos locales de Electron. En la aplicación de escritorio, las consultas GET pasan por un puente IPC limitado a los endpoints de lectura utilizados por esta interfaz, de modo que no requieren relajar CORS en la API.
