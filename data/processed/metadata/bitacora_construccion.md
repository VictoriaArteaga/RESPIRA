# Bitácora de construcción

- Pipeline `1.0.0`; calendario `cal-v1-parcial-2016-2022`. Fuentes leídas en solo lectura desde `C:\Users\MARIA VICTORIA\Desktop\universidad\SEMESTRES\QUINTO SEMESTRE\Diseño de interfaces\FINALES\RESPIRA - copia\data`.
- Etapa 1 (lectura): SIVIGILA 2012-2022 (hoja de detalle por año) y DANE 2005-2017 / 2018-2042 a `data/interim/` (regenerable, ignorado por git).
- Etapa 2: normalización y banderas territoriales; grupos de repetición (1705 filas, 827 grupos); agregación municipio-semana; población; V1.
- V1 construido: (36736, 39); V2: (36736, 52), temperatura VALIDA 1002; V3: (36736, 50).
- Estados municipales de temperatura: {'SIN_ESTACION': 48, 'ESTACION_VALIDADA': 10, 'ESTACION_COBERTURA_INSUFICIENTE': 4, 'SERIE_NO_CONFIABLE': 1, 'SIN_ESTACION_VALIDADA': 1}. Estados de precipitación: {'ESTACION_CANDIDATA': 37, 'SIN_ESTACION': 20, 'ESTACION_COBERTURA_INSUFICIENTE': 7}.
- Evidencia Aldana: {'dias_con_3_variables': 4016, 'dias_min_igual_max': 4016, 'dias_media_mayor_max': 4016, 'dias_min_mayor_max': 0}. Evidencia Chachagüí: {'codigo': 52045020, 'nombre': 'AEROPUERTO ANTONIO NARIÑO [52045020]', 'municipio_catalogo': 'Chachaguí', 'latitud': 1.394083333, 'longitud': -77.29086111, 'altitud': 1796.0, 'otras_estaciones_catalogadas_en_el_municipio': '52040030', 'limites_municipales_disponibles': 'NO', 'ubicacion_dentro_del_municipio_demostrada': 'NO'}.
- Filas completas (t, lags, objetivo) por tabla supervisada: {'V1_SUMA_h2': 26219, 'V1_SUMA_h3': 25684, 'V1_ULTIMO_REPORTE_h2': 26179, 'V1_ULTIMO_REPORTE_h3': 25646, 'V2_SUMA_h2': 4313, 'V2_SUMA_h3': 4228, 'V2_ULTIMO_REPORTE_h2': 4311, 'V2_ULTIMO_REPORTE_h3': 4227}.
- Validaciones: 13 PASS, 3 WARN, 0 FAIL, 2 INFO (ver `validaciones.csv`).
- No se modificaron fuentes; no hubo imputación; no hubo conexión a PostgreSQL/Supabase; no se entrenó ningún modelo; no se hicieron commits.
