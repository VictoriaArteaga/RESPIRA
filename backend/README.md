# RESPIRA — Backend

RESPIRA es un proyecto académico que busca apoyar el monitoreo de infecciones respiratorias agudas (IRA) en menores de cinco años en el departamento de Nariño. El backend incluye los endpoints iniciales, el mapa estadístico de riesgo municipal y el canal endémico de las semanas 3 y 4.

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
- No se necesita PostgreSQL para el modo académico local.
- PostgreSQL 14+ es opcional si se configura una instancia propia.
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

## Configuración de PostgreSQL (Supabase)

El backend usa exclusivamente PostgreSQL (Supabase, Session Pooler). Copia `.env.example` como `.env` y completa `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`; la aplicación no arranca si falta alguna. La contraseña se escapa automáticamente al construir la URL y no aparece en logs.

El esquema se gestiona con Alembic (`migrations/`). Con el entorno virtual activo y `.env` configurado:

```powershell
python -m alembic upgrade head      # crea/actualiza tablas
python -m alembic current           # revisión aplicada
python -m alembic downgrade base    # revierte (elimina las tablas: usar solo con aprobación)
```

La migración `0001` crea `municipalities` e `ira_cases` con clave foránea, índices, `UNIQUE (municipality_id, year, epidemiological_week)` y `CHECK` de semana 1–53 y casos ≥ 0. Al iniciar, la API **no** crea tablas ni carga datos. `DB_CREATE_TABLES` y `DB_SEED_SIMULATED` existen solo para desarrollo controlado y no deben activarse contra Supabase.

No agregues el archivo `.env` al control de versiones. El archivo está ignorado por Git. La siembra se ejecuta dentro de una transacción; si falla la carga, el error impide que el inicio se reporte como exitoso. Para regenerar el archivo de prueba de forma reproducible:

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

Niveles de acceso: **Público** (sin sesión), **Sesión** (cuenta activa con rol `analyst` o `admin`; se envía `Authorization: Bearer <token>`) y **Admin** (solo rol `admin`). Sin sesión válida la API responde 401 y, con un rol insuficiente, 403.

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/api/health` | Público | Estado de la API |
| POST | `/api/auth/register` | Público | Solicita una cuenta: responde 202 y la cuenta `analyst` queda pendiente de aprobación |
| POST | `/api/auth/login` | Público | Devuelve un token Bearer si la cuenta está activa (403 si está pendiente o desactivada; 429 tras demasiados intentos) |
| GET | `/api/auth/me` | Sesión | Perfil de la cuenta autenticada |
| POST | `/api/auth/logout` | Sesión | Cierra la sesión y revoca los tokens de la cuenta (204) |
| GET | `/api/admin/users` | Admin | Lista de cuentas |
| PATCH | `/api/admin/users/{user_id}` | Admin | Cambia el rol o el estado (`is_active`) de otra cuenta; 400 si es la propia, 404 si no existe |
| GET | `/api/municipalities` | Sesión | Lista de municipios |
| GET | `/api/municipalities/{municipality_id}` | Sesión | Detalle de un municipio |
| GET | `/api/cases` | Sesión | Casos, filtrables por `municipality_id`, `year` y `epidemiological_week` |
| GET | `/api/dashboard` | Sesión | Resumen calculado desde los registros de la base de datos |
| GET | `/api/risk-map?year=2025&week=40` | Sesión | Comparación estadística de riesgo por municipio |
| GET | `/api/alerts?year=2025&week=40` | Sesión | Alertas moderadas y altas basadas en los umbrales del mapa |
| GET | `/api/municipalities/{id}/risk` | Sesión | Detalle de riesgo para un municipio y periodo |
| GET | `/api/municipalities/{id}/endemic-channel?year=2025` | Sesión | Casos observados y percentiles históricos por semana |

Los filtros de casos se pueden combinar, por ejemplo: `/api/cases?municipality_id=1&year=2025`.

El resumen del dashboard informa el total de municipios, suma de casos, promedio de casos por municipio a lo largo de los registros, municipio con más casos acumulados, última semana epidemiológica y total de registros. El riesgo compara los casos de una semana con la media de esa misma semana en años anteriores (bajo <20%, moderado 20–<50%, alto ≥50%). El canal calcula mediana y percentiles 25, 75 y 90 por semana a partir de registros de años previos. Son estadísticas descriptivas; no se generan predicciones ni se utiliza IA.

## Pruebas

Desde `backend` y con las dependencias instaladas:

```powershell
python -m pytest
```

Las pruebas usan SQLite en memoria, configurado solo en `tests/conftest.py`, y no requieren conexión a PostgreSQL. SQLite no se usa en ejecución real.

Las alertas clasifican como vigilancia una variación de 20% a menos de 50% y como riesgo alto una variación de 50% o más frente a la media histórica de la misma semana. Los niveles reutilizan los umbrales del mapa y no son predicciones.

## Autenticación

Autenticación propia con FastAPI (sin Supabase Auth). Las contraseñas se guardan con Argon2id en la tabla `users`, separada de las tablas epidemiológicas.

Variables nuevas en `.env`: `JWT_SECRET_KEY` (obligatoria, mínimo 32 caracteres), `JWT_ALGORITHM` (`HS256` por defecto; solo HS256/384/512) y `ACCESS_TOKEN_EXPIRE_MINUTES` (30 por defecto). Genera la clave con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

| Endpoint | Acceso |
|---|---|
| `POST /api/auth/register` | Público; responde siempre 202 y crea una cuenta `analyst` **inactiva** pendiente de aprobación (el rol del cliente se rechaza) |
| `POST /api/auth/login` | Público; devuelve un token Bearer solo a cuentas activas (403 si está pendiente o desactivada) |
| `GET /api/auth/me`, `POST /api/auth/logout` | Sesión válida |
| `GET /api/admin/users`, `PATCH /api/admin/users/{id}` | Solo `admin` (rol y estado de cuentas) |
| Resto de `/api/*` (excepto `/api/health`) | `analyst` o `admin` |

**Cierre de sesión:** cada usuario tiene `token_version`; el token lo incluye (`tv`). El logout, un cambio de rol o la desactivación incrementan el contador y todos los tokens anteriores dejan de valer (se comprueba en cada petición). Limitación: el logout cierra la sesión en todos los dispositivos, y un token no revocado sigue siendo válido hasta su expiración.

**Primer administrador** (tras aplicar la migración `0002`), de forma interactiva, sin contraseñas por defecto:

```powershell
python -m scripts.create_admin
```

Migración: `python -m alembic upgrade head` crea la tabla `users` (no modifica `municipalities` ni `ira_cases`); `python -m alembic downgrade 0001` la elimina.

**Aprobación de cuentas:** las solicitudes de registro quedan con `is_active=false` (también es el valor por defecto en la base). Un administrador las activa con `PATCH /api/admin/users/{id}` enviando `{"is_active": true}`; el listado `GET /api/admin/users` muestra el estado.

**Enumeración de correos:** el registro responde 202 con el mismo cuerpo exista o no el correo, y un correo existente no se modifica ni se notifica. Los errores de validación (422) no dependen del correo. Quedan dos señales residuales: el 403 de inicio de sesión (solo se obtiene con la contraseña correcta) y diferencias de tiempo mínimas (se iguala el coste del hash).

**Limitación de intentos** (en memoria, por proceso; se reinicia con el backend): 5 fallos por IP+correo y 20 por IP cada 15 minutos en el inicio de sesión (429 con `Retry-After`; un acceso correcto reinicia el contador del par), y 10 solicitudes de registro por IP por hora. Es un bloqueo temporal, nunca permanente. No usa `X-Forwarded-For`; tras un proxy habría que configurarlo. No se comparte entre varios workers.

Limitaciones conocidas: no hay verificación de correo ni recuperación de contraseña.
