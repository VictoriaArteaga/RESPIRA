# Directorio `data/`

Separación entre fuente original y derivados:

| Ruta | Contenido | ¿En Git? |
|---|---|---|
| `data/SIVIGILA/`, `data/*Diaria/`, `data/*.xls(x)`, `data/*.csv` (catálogos) | **Originales**. Solo lectura: nunca se modifican, mueven ni sobrescriben. | No (ignorados) |
| `data/scripts/` | Scripts de auditoría reproducibles (`auditar_*.py`). | Sí |
| `data/reports/` | Salidas de auditoría. | Sí |
| `data/processed/` | Derivados documentados (piloto exploratorio de la auditoría). No es dataset productivo. | Sí |

Los originales se obtienen de sus proveedores (INS-SIVIGILA, IDEAM, DANE) y se colocan aquí localmente. Su procedencia se acredita con SHA-256 (`reports/cuarta_auditoria/sha256_fuentes.csv`; cada lote importado guarda el hash en `import_batch`). El esquema de la base de datos vive en las migraciones de Alembic (`backend/migrations/`), no en este directorio. Reglas de importación y validación: [docs/data-integration](../docs/data-integration/README.md).
