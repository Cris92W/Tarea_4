# ¿Mejoran las respuestas con el MCP y las Skills? Comparación de los dos modos

Las mismas 10 preguntas ([`preguntas.csv`](preguntas.csv)) se le hicieron a Claude Code (Sonnet) sin y con los
componentes del proyecto. Resultados completos: [`resultados.csv`](resultados.csv). Tablas generadas por script:
[`tablas.md`](tablas.md). Registro de cada ejecución: [`evidencias_ia/evaluacion/`](../evidencias_ia/evaluacion/).

## Diseño

| | Modo A: sin MCP ni Skills | Modo B: con MCP y Skills |
|---|---|---|
| Herramientas habilitadas | Solo búsqueda web: `WebSearch` y `WebFetch` | El servidor MCP `bcrp`, las 4 Skills del proyecto, terminal y archivos (`Bash`, `Read`, `Glob`, `Grep`, `Write`) y la misma búsqueda web |
| Dónde corre | Una carpeta vacía: no hay archivos del proyecto que leer | Una copia limpia del proyecto, con los microdatos originales pero sin ninguna salida ni la referencia de la Sesión 16 |
| Igual en los dos | Modelo Sonnet, la misma instrucción, una sesión nueva por pregunta (`--no-session-persistence`), sin la memoria automática de Claude Code y respuesta en JSON con `valor`, `valor_2`, `fuente` e `interpretacion` | |

- **Respuestas esperadas fijadas antes de correr.** Se calcularon sin el código evaluado (`respuestas_esperadas.py`:
  el BCRP directo de su API y la ENAHO directo del archivo del INEI) y se guardaron en el commit `35151e1` antes de
  la primera ejecución.
- **Tolerancias y criterios fijados de antemano** (en `preguntas.csv`). En la combinada c1 se exigen los dos valores;
  con uno solo, la respuesta es parcial. En c2 se exigen el coeficiente y una interpretación de asociación negativa
  sin afirmar causalidad.
- **Revisión manual de una calificación.** La regla automática para la interpretación de c2 buscaba las palabras
  «negativa» o «inversa». La respuesta del modo B dice «los departamentos con más pobreza tienden a tener menos
  crédito… no causal», que cumple el criterio, así que se calificó como correcta. El cambio y su motivo están en
  [`revision_manual.csv`](revision_manual.csv); la nota automática sigue en la columna `resultado_automatico`.

## Resultados

| Modo | Correctas | Parciales | Incorrectas | Sin respuesta | Segundos en promedio | Usó el MCP | Usó Skills |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: sin MCP ni Skills | 6 | 0 | 2 | 2 | 26.9 | 0 | 0 |
| B: con MCP y Skills | 10 | 0 | 0 | 0 | 20.6 | 6 | 4 |

| Tipo de pregunta | A | B |
|---|---|---|
| BCRP (4) | 2 de 4 | 4 de 4 |
| ENAHO (4) | 3 de 4 | 4 de 4 |
| Combinadas (2) | 1 de 2 | 2 de 2 |

| Pregunta | Esperado | Modo A | Modo B |
|---|---|---|---|
| b1 Inflación de Lima a 12 meses, dic-2024 | 1.97 % | 1.97 ✔ (de memoria, 6 s) | 1.97 ✔ (`serie`, 11 s) |
| b2 Tasa de referencia, dic-2024 | 5.00 % | 5.00 ✔ (de memoria, 6 s) | 5.00 ✔ (`buscar_series`, `serie`, 12 s) |
| b3 Crecimiento del PBI real 2024 | 3.52 % | 3.3 ✘ (20 s) | 3.5 ✔ (`buscar_series`, `resumen`, `serie`, 14 s) |
| b4 Crédito directo en Piura, fin de 2024 | 9 049.1 millones | 9 241.6 ✘ (39 s) | 9 049.1 ✔ (`panel_departamental`, 11 s) |
| e1 Pobreza nacional 2024 | 27.6 % | 27.6 ✔ (web, 15 s) | 27.6 ✔ (web, 19 s) |
| e2 Pobreza rural 2024 | 39.3 % | 39.3 ✔ (web, 15 s) | 39.3 ✔ (web, 28 s) |
| e3 Pobreza rural de Piura 2024 | 41.52 % | sin respuesta (39 s) | 41.52 ✔ (`limpiando-enaho`, 25 s) |
| e4 Pobreza extrema 2024 | 5.5 % | 5.5 ✔ (web, 19 s) | 5.5 ✔ (`limpiando-enaho`, 25 s) |
| c1 Pobreza de Piura y crédito por habitante | 31.86 % y S/ 4 550.6 | 31.9 y 4 550.6 ✔ (86 s) | 31.86 y 4 550.6 ✔ (`cruzando-bcrp-enaho`, `panel_departamental`, 26 s) |
| c2 Spearman pobreza–crédito por habitante | −0.609 | sin respuesta (23 s) | −0.604 ✔ (`cruzando-bcrp-enaho`, `panel_departamental`, `serie`, 35 s) |

**Mejoraron** con el MCP y las Skills 4 preguntas: b3, b4, e3 y c2. **Ninguna empeoró.**

## Errores y comportamientos observados

- **Modo A, una cifra que ya no es la vigente (b3).** Respondió 3.3 %, la primera estimación que encontró en
  resultados de búsqueda sobre una nota de estudios del BCRP de inicios de 2025, sin abrir el PDF. La serie vigente
  del BCRP (PM04923AA) da 3.52 %. El MCP lee la serie actual.
- **Modo A, otra definición de la cifra (b4).** Dio S/ 9 241.6 millones, que sacó de los resúmenes de búsqueda de la
  «Síntesis de actividad económica» de la sucursal Piura del BCRP: no pudo abrir el PDF por una verificación
  antibots. Ese documento habla de «crédito», no de la serie de crédito directo, y el propio agente advirtió que no
  pudo confirmar que fuera lo mismo. El MCP trae la serie exacta, RD16184DA.
- **Modo A, indicadores que nadie publica (e3, c2).** La pobreza rural de Piura y la correlación entre 25
  departamentos hay que calcularlas con los microdatos. El modo A no tenía terminal ni datos y, en vez de inventar,
  respondió `null` y explicó qué le faltaba. Es el comportamiento correcto.
- **Modo A acertó una combinada (c1) gracias a terceros.** Encontró la pobreza de Piura (31.9 %) y su población
  (1 988 570 personas) en notas de prensa que citan un procesamiento de la ENAHO del Instituto Peruano de Economía, y
  el crédito en la tabla web del BCRP. Esas cifras coinciden exactamente con las de este proyecto: 87 598 + 545 980 =
  633 578 pobres, los mismos que da `limpiando-enaho`. Es una validación externa del pipeline, pero el modo A tardó
  86 s frente a 26 s del modo B y dependió de fuentes secundarias.
- **Modo B, la web para cifras publicadas.** En e1 y e2 respondió con búsqueda web sin activar las Skills: son cifras
  oficiales muy difundidas. Acertó, pero esas dos preguntas no midieron el aporte de las Skills.
- **Modo B, sin respuestas incorrectas.** El valor de c2 (−0.604) difiere del esperado (−0.609) porque la skill usa la
  pobreza redondeada a 2 decimales, que empata a Lima y Ucayali; está dentro de la tolerancia y se explica en
  [`informes/verificacion.md`](../informes/verificacion.md).

## Tiempo

El modo B fue más rápido en promedio (20.6 s frente a 26.9 s), aunque procesa microdatos. El modo A gana en las
preguntas que el modelo sabe de memoria (b1 y b2, 6 s), pero se demora cuando tiene que buscar y leer páginas (b4 39 s,
c1 86 s). En el modo B, las preguntas que activaron la skill de limpieza (e3 y e4) incluyen la limpieza completa de
la base de la ENAHO, unos 25 s, y aun así tardan menos que las búsquedas largas del modo A.

## Conclusión

Con el MCP y las Skills, Claude Code pasó de 6 a 10 respuestas correctas, eliminó las 2 incorrectas y las 2 sin
respuesta, y tardó menos en promedio. El aporte se concentra donde la búsqueda web no basta: series oficiales
revisadas o de detalle departamental (b3, b4) e indicadores que solo existen si se calculan con los microdatos (e3,
c2). Para cifras nacionales muy publicadas (inflación, tasa de referencia, pobreza nacional y rural), la memoria del
modelo o la búsqueda web alcanzan. Los dos modos fueron honestos: cuando no pudieron verificar una cifra devolvieron
`null` en vez de estimarla.

**Límites de esta evaluación:**
- Son 10 preguntas y una sola ejecución por pregunta y modo; con otra corrida algún resultado podría cambiar.
- La web cambia con el tiempo.
- El modo B también tenía búsqueda web, así que la diferencia mide el aporte del MCP y las Skills sumados a lo que
  ya tenía el modo A.
