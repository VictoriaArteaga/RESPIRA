# Cuarta auditoría y validación del piloto

Este directorio explica y conserva los resultados de la cuarta auditoría del piloto RESPIRA. No reemplaza ni modifica la segunda auditoría preservada en `docs/data-audit/segunda-auditoria/`.

## Ejecutar

Desde la raíz del repositorio RESPIRA, con el Python que tiene `openpyxl` instalado:

```powershell
.\backend\.venv\Scripts\python.exe .\data\scripts\auditar_cuarta_respira.py
```

Si se usa otro entorno, el intérprete debe tener `openpyxl` instalado.

Opcionalmente se indican la raíz y carpeta de resultados:

```powershell
python data/scripts/auditar_cuarta_respira.py --root . --out reports/cuarta_auditoria
```

El script solo abre fuentes, libros y CSV para lectura. Las salidas deterministas se escriben en `reports/cuarta_auditoria/`; no procesa datos personales de manera impresa ni los exporta.

## Resultados

- `resumen_validaciones.md`: conteo de PASS, FAIL y WARNING/PENDING con interpretación.
- `validaciones.csv`: registro reproducible de cada comprobación.
- `calendario_semana_epi.csv`: comparación de límites actuales y calendario INS documentado para semanas 1–52 de 2016 y 2022.
- `filas_repeticion_sivigila.csv`: solo campos analíticos necesarios de renglones que comparten municipio-año-semana-UPGD-sede; no contiene nombre/teléfono/contacto.
- `cobertura_meteorologica.csv`: fecha diaria válida, duplicados de fecha y semanas bajo el umbral de cobertura por estación-variable-año.
- `sha256_fuentes.csv`: snapshot de hashes actuales y, donde existía, comparación con hash anterior conocido.
- `piloto_respira_2016_2022_auditado_v2.csv`: derivado versionado que conserva filas y valores, pero corrige la etiqueta engañosa de “duplicado” para la repetición de proveedor-semana. El CSV piloto original no se sobrescribe.

## Interpretación

`PASS` valida una regla técnica local; no certifica la calidad científica de la fuente. `WARNING` identifica faltantes o repetición de reportes para conservar y revisar. `PENDING` identifica metadatos/rangos que no se deben inventar. Los hashes sin baseline anterior son snapshots, no prueba retrospectiva de que la fuente nunca cambió. El calendario usa evidencia INS: domingo–sábado y SE52 oficial 25–31 de diciembre en ambas anualidades piloto; para extender a años con posible SE53, consultar calendario anual correspondiente.

El informe principal es `reports/cuarta_auditoria_respira.md`. Los resultados automáticos están en `reports/cuarta_auditoria/`.
