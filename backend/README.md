# RESPIRA — Backend

RESPIRA es un proyecto académico que busca apoyar el monitoreo de infecciones respiratorias agudas (IRA) en menores de cinco años en el departamento de Nariño. Este backend implementa exclusivamente la configuración y los endpoints iniciales de las semanas 1 y 2.

> **Aviso:** Los registros que incluye el proyecto son sintéticos y se usan únicamente para pruebas. No son datos de SIVIGILA ni información epidemiológica real.

## Tecnologías

- Python 3.10 o posterior
- FastAPI y Uvicorn
- PostgreSQL, SQLAlchemy y Psycopg
- Pydantic y pydantic-settings
- Pandas y NumPy para generar y cargar el conjunto de prueba
- Pytest y HTTPX para pruebas

## Requisitos

- Python 3.10+
- PostgreSQL 14+ ejecutándose localmente
- Git (opcional, para clonar el repositorio)

## Instalación

Desde la raíz del repositorio, entra al directorio `backend`:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En Linux, activa el entorno con `source .venv/bin/activate`.

## Configuración de PostgreSQL y entorno

Crea una base de datos vacía para el proyecto:

```sql
CREATE DATABASE respira;
```

Copia `.env.example` como `.env` y actualiza la URL con el usuario y contraseña locales de PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/respira
CORS_ORIGINS=["http://localhost:5173"]
```

No agregues el archivo `.env` al control de versiones. Al iniciar, la API crea las tablas y carga el CSV sintético si la tabla de casos está vacía. La siembra se ejecuta dentro de una transacción; si falla la carga, el error impide que el inicio se reporte como exitoso. Para regenerar el archivo de prueba de forma reproducible:

```powershell
python scripts/generate_synthetic_data.py
```

El CSV contiene 10 municipios, semanas epidemiológicas 1–52 de 2023–2025 y una columna `data_source` con el texto `DATOS SINTÉTICOS DE PRUEBA`.

## Ejecutar la API

Con PostgreSQL en ejecución y `.env` configurado:

```powershell
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000` y Swagger UI en `http://localhost:8000/docs`.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Estado de la API |
| GET | `/api/municipalities` | Lista de municipios |
| GET | `/api/municipalities/{municipality_id}` | Detalle de un municipio |
| GET | `/api/cases` | Casos, filtrables por `municipality_id`, `year` y `epidemiological_week` |
| GET | `/api/dashboard` | Resumen calculado desde los registros de la base de datos |

Los filtros de casos se pueden combinar, por ejemplo: `/api/cases?municipality_id=1&year=2025`.

El resumen del dashboard informa el total de municipios, suma de casos, promedio de casos por municipio a lo largo de los registros, municipio con más casos acumulados, última semana epidemiológica y total de registros. No genera predicciones, niveles de riesgo ni alertas.

## Pruebas

Desde `backend` y con las dependencias instaladas:

```powershell
python -m pytest
```

Las pruebas usan SQLite local y no requieren una instancia de PostgreSQL.
