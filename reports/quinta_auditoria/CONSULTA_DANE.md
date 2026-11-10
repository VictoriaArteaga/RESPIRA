# Consulta al DANE — Proyecciones municipales de población 0–4 años (Nariño)

> **BORRADOR PARA REVISIÓN. NO ENVIADO.** Requiere revisión y autorización de la autora antes de cualquier envío. No hay respuesta del DANE: lo marcado como «pendiente» no está confirmado.

**Fecha del borrador:** 5 de noviembre de 2026
**Proyecto:** RESPIRA — análisis de infecciones respiratorias agudas en menores de cinco años, Nariño
**Remitente:** [nombre y datos de contacto de la autora — completar antes del envío]
**Destinatario sugerido:** DANE — Dirección de Censos y Demografía, proyecciones de población (a confirmar)

## 1. Contexto

Usamos dos libros de proyecciones municipales por área, sexo y edad simple:

- `DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx` (hoja `NuevaMpal`, 2005–2017).
- `PPED-AreaSexoEdadMun-2018-2042_VP.xlsx` (hoja `PobMunicipalxáreaSexoEdad`, 2018–2042; la hoja `PPED` indica actualización al 30 de julio de 2025).

Calculamos la población de 0 a 4 años con el área «Total» y la suma de las edades simples 0, 1, 2, 3 y 4, para los 64 municipios de Nariño, años 2012–2022. Verificamos que Total = Cabecera + Centros poblados y que el total de 0–4 es igual a hombres + mujeres.

## 2. Preguntas

### Tema A — Continuidad entre las dos series

**Antecedente.** Al pasar de 2017 (primer libro) a 2018 (segundo libro), la población 0–4 de Nariño sube de 126.835 a 134.253 (+5,85%); por municipio la mediana es +8,24%, 53 de 64 municipios suben más de 5% y 3 bajan más de 5%. Dentro de cada libro las variaciones anuales son pequeñas (mediana −0,19% de 2016 a 2017 y −1,66% de 2018 a 2019). Ejemplos: Tumaco 25.092 → 28.366; Chachagüí 1.042 → 1.122; Pasto 25.756 → 25.104.

1. **A1.** ¿El salto entre 2017 y 2018 se debe al cambio de base de las proyecciones (de la serie con base en el censo de 2005 a la basada en el CNPV 2018)? *Por qué:* decidimos **no reescalar** la serie y marcar el libro de origen; queremos documentar la causa.
2. **A2.** ¿Existe una serie empalmada o retroproyectada oficial 2005–2017 con la base actual? ¿Dónde se publica?
3. **A3.** Si no existe, ¿qué recomienda el DANE para análisis que crucen 2017 y 2018 (por ejemplo, usar solo la serie 2018+ y no mezclarlas)?

### Tema B — Versiones y vigencia

4. **B1.** Los archivos terminan en `_VP`. ¿Qué significa? ¿Son versión preliminar o definitiva?
5. **B2.** ¿Qué cambios hubo entre la actualización de julio de 2025 de la hoja `PPED` y la fecha de publicación del 8 de agosto de 2025 que consta en la página de proyecciones? ¿Se prevén nuevas revisiones de 2018–2042?
6. **B3.** ¿Cómo deben citarse y versionarse estos libros para que otros puedan reproducir el cálculo?

### Tema C — Uso para tasas en municipios pequeños

**Antecedente.** 13 municipios de Nariño tienen menos de 500 menores de 5 años en 2022 (el mínimo observado es 283 en 2017) y 40 menos de 1.000.

7. **C1.** ¿Qué precisión tienen las proyecciones por edad simple en municipios con poblaciones muy pequeñas? ¿Recomienda el DANE usarlas para tasas semanales en esos municipios o agregarlas?
8. **C2.** ¿La proyección corresponde a la población residente? ¿Incluye o excluye población flotante o migrante, y cómo se trata la migración posterior a 2018?

### Tema D — Interpretación de la estructura del libro

9. **D1.** En el libro 2005–2017 los campos territoriales están en el orden `DP, DPNOM, DPMP, MPIO` y en el libro 2018–2042 en `DP, DPNOM, MPIO, DPMP`. Confirmamos que `MPIO` es el código DIVIPOLA de 5 dígitos y `DPMP` el nombre del municipio en ambos. ¿Es correcto?
10. **D2.** El libro 2018–2042 contiene 4 filas adicionales sin área tras los 84.225 registros (probablemente notas). ¿Es así?
11. **D3.** ¿Disponen de una versión del libro nacional `PPED-AreaSexoEdadNac-2018-2070.xlsx` y del libro departamental 2005–2017 que se citaron en una revisión anterior? No lo necesitamos para el cálculo municipal, pero quisiéramos documentar su procedencia.

## 3. Formato de respuesta solicitado

Una respuesta por numeral con el documento oficial que la respalda. Si algún punto no puede contestarse, indíquenlo para registrarlo como limitación.

## 4. Antecedentes disponibles

`reports/quinta_auditoria/EVALUACION_POBLACION_DANE.md` e `INFORME_GENERAL.md` (sección 4).
