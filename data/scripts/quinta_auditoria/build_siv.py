import pandas as pd, json
R = "C:/Users/MARIA VICTORIA/Desktop/universidad/SEMESTRES/QUINTO SEMESTRE/Diseño de interfaces/FINALES/RESPIRA/"
OUT = R + "reports/quinta_auditoria/"
cols = {y: set(json.load(open(f'cols_{y}.json'))['cols']) for y in range(2012, 2023)}


def pres(names):
    allys = [y for y in range(2012, 2023) if all(n in cols[y] for n in names)]
    return 'todos 2012-2022' if len(allys) == 11 else ','.join(map(str, allys))


V = 'Verificada'
U = 'Utilizable con restricciones'
P = 'Pendiente de validación'
N = 'No utilizable actualmente'
rows = []


def add(var, names, sig, est, uso, obs, evid):
    rows.append(dict(variable=var, presente_en_anios=pres(names), significado_operativo=sig, estado=est,
                     uso_en_indicador_o_modelo=uso, observaciones=obs, evidencia=evid))


add('cod_eve', ['cod_eve'], 'Código de evento (995 = morbilidad por IRA, notificación colectiva).', V, 'Filtro',
    '100% de las filas = 995 en los 11 libros (p. ej. 231,881 filas de datos en 2016; 235,738 en 2022).',
    'Escaneo 5.ª auditoría de las hojas de detalle; reports/auditoria_sivigila_995_2012_2022.md')
add('nom_eve', ['nom_eve'], 'Nombre del evento.', U, 'Control',
    'Etiqueta distinta entre años: «MORBILIDAD POR IRAG» en las primeras filas de 2012 y «MORBILIDAD POR IRA» en 2016, 2021 y 2022 (observado en filas iniciales, no tabulado). El código 995 es constante.',
    'Primeras filas de 2012, 2016, 2021, 2022')
add('fec_not', ['fec_not'], 'Fecha de notificación (no ocurrencia ni inicio de síntomas).', U, 'No usar para asignar semana',
    'Formato heterogéneo: número serial Excel (2012, 2016, 2022) y texto dd/mm/aaaa en filas de 2021.',
    'Primeras filas 2012/2016/2021/2022; reports/diccionario_sivigila_995.csv')
add('semana', ['semana'], 'Semana epidemiológica reportada (domingo–sábado).', V, 'Clave temporal',
    'Rango 1–52 en la mayoría de años; 53 solo en 2014 (123 filas de Nariño) y 2020 (124 filas), coherente con la regla del 4 de enero (años de 53 semanas: 2014 y 2020). En el libro 2021 hay 39 filas nacionales con semana 53 (0 en Nariño), anómalas para un año de 52 semanas.',
    'Escaneo 5.ª auditoría (conteo por semana de cada libro)')
add('año', ['ano'], 'Año epidemiológico.', V, 'Clave temporal',
    'Coincide con el año del libro en el 100% de las filas de Nariño (0 discordantes en 11 años). El nombre contiene «ñ» (riesgo de codificación al exportar).',
    'Escaneo 5.ª auditoría')
add('cod_pre', ['cod_pre'], 'Código del prestador/UPGD.', U, 'Solo capa restringida (control de reportes repetidos)',
    'Formato heterogéneo: 9 o 10 dígitos, con y sin cero a la izquierda (2012 hoja «995 52» sin cero vs hoja «Base Recibida» con cero; 2022 sin cero vs 2016 con cero). Requiere normalización. Entre 144 y 165 UPGD distintos por año en Nariño.',
    'Primeras filas 2012/2016/2022; escaneo')
add('cod_sub', ['cod_sub'], 'Subíndice/sede del prestador.', U, 'Solo capa restringida',
    'Valor «1» en 2012/2022 frente a «01» en 2016/2021 (número vs texto).', 'Primeras filas')
add('cod_mun', ['cod_mun'], 'Código DIVIPOLA del municipio notificador (no residencia).', U, 'Clave territorial',
    '64 municipios de Nariño por año (2013–2022). Inconsistencias código/nombre: 2 filas de 2012 con código 52838 (Túquerres) y ndep_notif=BOYACÁ (Tununguá); 7 filas de 2014 con 52356 (Ipiales) y ndep_notif=BOGOTÁ; 1 fila de 2012 con código 52000 (nmun_notif=PASTO). Debe cruzarse con ndep_notif/nmun_notif. El libro 2012 guarda códigos sin cero inicial.',
    'Escaneo 5.ª auditoría (filtro: cod_mun que inicia con 52; no se detectan filas de Nariño con código de otro departamento porque no se filtró por nombre)')
add('ndep_notif', ['ndep_notif'], 'Nombre del departamento notificador.', U, 'Control de consistencia',
    'Permite detectar las 9 filas con código/departamento incongruente.', 'Escaneo')
add('nmun_notif', ['nmun_notif'], 'Nombre del municipio notificador.', U, 'Control de consistencia',
    'Variantes de nombre (p. ej. SANTA BARBARA (ISCUANDE), MAGUI (PAYAN)); no unir por nombre.', 'Escaneo')
add('num_con', ['num_con'], 'Consecutivo del reporte de la UPGD (no identifica pacientes).', P,
    'Orden de reportes dentro de un grupo repetido',
    'Evidencia nueva: crece +1 entre semanas consecutivas de una misma UPGD en 86–89% de los pares en 2019–2022 y en 60–71% en 2012–2016: se comporta como contador secuencial de reportes por UPGD. 1 valor nulo en 2012. No resuelve por sí solo si un reporte repetido corrige o suma.',
    'Análisis 5.ª auditoría sobre 11 libros (Nariño)')
add('demanda', ['demanda'], 'Campo sin descripción localizada.', N, 'No usar', 'Solo existe en el libro 2012.', 'Cabecera 2012')
add('iracext_1', ['iracext_1'], 'IRA consulta externa/urgencias, menores de 1 año (estructura INS 2016).', U,
    'Numerador candidato (suma con _2 y _3)',
    'Presente en todos los años. Celdas vacías (no cero) en filas de Nariño: 2013 (155 filas con al menos uno de los tres campos vacío), 2014 (11), 2016 (34), 2017 (34), 2018 (38); 0 en 2012, 2015 y 2019–2022. Una suma que ignora vacíos las convierte en cero silenciosamente. Ninguna fila vacía cae en Chachagüí, Funes o Samaniego en 2016/2022.',
    'Escaneo 5.ª auditoría; reports/cuarta_auditoria_respira.md')
add('iracext_2', ['iracext_2'], 'IRA consulta externa/urgencias, 1 año.', U, 'Numerador candidato', 'Ver iracext_1.', 'Ídem')
add('iracext_3', ['iracext_3'], 'IRA consulta externa/urgencias, 2–4 años.', U, 'Numerador candidato', 'Ver iracext_1.', 'Ídem')
add('iracext_4..iracext_7', ['iracext_4', 'iracext_5', 'iracext_6', 'iracext_7'],
    'IRA consulta externa/urgencias en grupos de 5 años o más.', P, 'Fuera del alcance (<5 años)',
    'Significado por grupo no re-verificado en esta auditoría.', 'Cabeceras')
add('tot_iraext', ['tot_iraext'], 'Total IRA consulta externa/urgencias (todas las edades).', P, 'Control de suma',
    'Ausente en el libro 2012. No se verificó que iguale la suma de iracext_1..7.', 'Cabeceras 2012 vs 2013–2022')
add('totcext_1..totcext_3', ['totcext_1', 'totcext_2', 'totcext_3'],
    'Total de consultas externas/urgencias (todas las causas) por grupo <1, 1 y 2–4 años (inferido por nombre de campo).',
    P, 'Denominador candidato (proporción IRA/consultas)',
    'Presente en todos los años. Permitiría medir IRA como proporción de las consultas del mismo prestador y no solo como conteo. En Nariño la razón IRA/consultas (0–4) baja de 0.26 (2012) a 0.04 (2020) y se recupera a 0.18 (2022). Semántica por confirmar con el formulario 995.',
    'Etiqueta «CE» en la fila 1 de la hoja ACUMULADO 2021; escaneo 5.ª auditoría')
add('totcext_4..totcext_7, tot_exturg', ['totcext_4', 'totcext_5', 'totcext_6', 'totcext_7', 'tot_exturg'],
    'Total de consultas externas/urgencias en los grupos restantes y total general.', P, 'No usado',
    'tot_exturg ausente en 2012.', 'Cabeceras')
add('grupoh_1..grupoh_7, tot_irag', ['grupoh_1', 'tot_irag'],
    'Hospitalizaciones por IRAG por grupo de edad (etiqueta «IRAG» en la fila 1 de 2021).', P,
    'Posible objetivo alternativo (gravedad)', 'tot_irag ausente en 2012. Conteos pequeños; no evaluados.',
    'Fila 1 hoja ACUMULADO 2021')
add('hospital_1..hospital_7, tot_cau_h', ['hospital_1', 'tot_cau_h'],
    'Hospitalizaciones por todas las causas (etiqueta «TH» en 2021).', P, 'No usado',
    'Semántica inferida de etiquetas parciales.', 'Fila 1 hoja ACUMULADO 2021')
add('irauci_1..irauci_7, tot_irauci', ['irauci_1', 'tot_irauci'],
    'Hospitalizaciones en UCI por IRAG (etiqueta «IRAG UCI»).', P, 'No usado',
    'Conteos esperablemente muy bajos.', 'Fila 1 hoja ACUMULADO 2021')
add('totuci_1..totuci_7, tot_h_uci', ['totuci_1', 'tot_h_uci'], 'Hospitalizados en UCI por todas las causas.', P,
    'No usado', 'Semántica inferida.', 'Cabeceras')
add('mteira_1..mteira_7, tot_mu_ira', ['mteira_1', 'tot_mu_ira'], 'Mortalidad por IRA por grupo de edad.', P, 'No usado',
    'Eventos raros; no apto como objetivo semanal municipal.', 'Cabeceras')
add('mtetot_1..mtetot_7, tot_muerte', ['mtetot_1', 'tot_muerte'], 'Mortalidad por todas las causas.', P, 'No usado',
    'Semántica inferida.', 'Cabeceras')
add('ajuste', ['ajuste'], 'Código de ajuste del registro.', P, 'Marcador de revisión',
    'En Nariño solo toma los valores 0 y 7. El valor 7 aparece en 3–139 filas por año (139 en 2013; 10 en 2021). Solo 92 de los 827 grupos de reporte repetido (11%) contienen una fila con ajuste 7, de modo que el ajuste NO explica la mayoría de las repeticiones. Significado de 7 para el evento 995 no confirmado en esta auditoría.',
    'Análisis 5.ª auditoría (grupos repetidos)')
add('fec_aju', ['fec_aju'], 'Fecha de ajuste.', P, 'Marcador de revisión', 'Formato mixto (serial/texto).', 'Primeras filas')
add('diligencia, cargo, telefono, correo', ['diligencia', 'cargo', 'telefono', 'correo'],
    'Datos de la persona que diligencia el reporte.', N, 'EXCLUIR (datos personales/contacto)',
    'No se copiaron a ningún archivo derivado de esta auditoría. Los libros los contienen en claro.', 'Cabeceras')
add('nit_upgd, nom_upgd', ['nit_upgd', 'nom_upgd'], 'Identificación de la institución prestadora.', N,
    'Solo capa restringida', 'No incluir en datasets analíticos compartidos.', 'Cabeceras')
add('version', ['version'], 'Versión del formato de captura.', U, 'Control de versión de esquema',
    'Presente en 2013–2021; ausente en 2012 y 2022. Valor «SIVIGILA - 2016 - VERSIÓN: 1.1» en 2016.', 'Cabeceras')
add('cod_dep', ['cod_dep'], 'Código de departamento.', N, 'No usar', 'Solo existe en el libro 2019 (85 columnas).', 'Cabeceras')
add('sivigi2010', ['sivigi2010'], 'Campo sin descripción localizada.', N, 'No usar', 'Solo existe en el libro 2012.', 'Cabecera 2012')
pd.DataFrame(rows).to_csv(OUT + 'EVALUACION_VARIABLES_SIVIGILA.csv', index=False, encoding='utf-8-sig')
print(len(rows), 'filas de variables SIVIGILA')
