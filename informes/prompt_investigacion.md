Eres el agente de investigación socioeconómica de este proyecto. Responde con datos oficiales esta pregunta de
investigación:

«¿Qué grado de asociación hay entre la incidencia de la pobreza monetaria en 2024 y el crédito directo del sistema
financiero por habitante, y cómo varió ese crédito en términos reales entre 2020 y 2024 según el nivel de pobreza de
cada departamento en el Perú?»

Título del informe: «¿Hay menos crédito donde hay más pobreza?»

Cómo trabajar:

1. Primero interpreta la pregunta y escribe un plan de análisis en informes/plan_analisis.md: qué datos necesitas,
   de qué fuente, con qué herramienta, qué indicadores calcularás y qué gráficos harás.
2. Para los datos del BCRP usa las herramientas del servidor MCP bcrp. Para la ENAHO activa con la herramienta Skill
   las Skills del proyecto (limpiando-enaho, graficando-enaho, mapeando-enaho) y sigue sus instrucciones; para unir
   el BCRP con la ENAHO por departamento activa la skill cruzando-bcrp-enaho. No leas los archivos de las Skills con
   la terminal: actívalas. No hagas cuentas a mano ni copies cifras de una herramienta a otra: pásalas como archivos.
3. Produce al menos: el gráfico del BCRP (variación real del crédito por departamento), un gráfico de la ENAHO
   (pobreza por departamento), el mapa departamental de la pobreza y la dispersión del crédito por habitante frente a
   la pobreza. Destaca Piura.
4. Contrasta con fuentes oficiales: la validación de la ENAHO frente a la cifra oficial del INEI (27.6 %), la
   comparación del mapa con la referencia de la Sesión 16 y al menos una cifra del BCRP en su tabla web (el enlace
   fuente_web que devuelve el MCP).
5. Escribe informes/informe_final.md con estas secciones:
   1. Pregunta de investigación: la pregunta textual, el tema, el objetivo y la delimitación.
   2. Fuentes y metodología: datos, procesamiento e indicadores.
   3. Resultados: al menos 3 hallazgos con sus cifras.
   4. Visualizaciones: inserta las figuras con rutas relativas (../figuras/... y ../mapas/...).
   5. Interpretación.
   6. Limitaciones: cobertura temporal, calidad de los datos y alcance de las conclusiones.
   7. Reproducibilidad: scripts, archivos, códigos de serie y comandos.
   Cada cifra debe salir de un archivo o de una herramienta y citar su fuente (código de serie y periodo, o archivo).
   Si una cifra, un puesto o una comparación no está tal cual en los archivos de salida, calcúlala con un comando
   sobre esos archivos antes de escribirla; no la deduzcas a ojo. No presentes la asociación como causalidad.
6. Si una herramienta falla, no encuentra datos o devuelve algo incompatible, dilo en el informe y no inventes el
   resultado.

Al terminar, resume en pocas líneas qué herramientas MCP y qué Skills usaste y dónde quedó cada archivo.
