# Verificación manual de cifras del informe

El issue pide comprobar a mano al menos 3 afirmaciones numéricas del [informe](informe_final.md), con cifras de las
dos fuentes. Aquí van 5, todas tomadas del texto del informe: dos del BCRP, dos de la ENAHO y una que combina
ambas. Para cada una se indica dónde mirarla. La columna «Valor que encontré» la llena el estudiante al revisarla.

Además hay un recálculo automático e independiente del código del proyecto: el BCRP directo de su API y la ENAHO
directo del archivo del INEI. Coinciden 7 de 7 cifras ([`verificacion_automatica.md`](verificacion_automatica.md)).

| # | Afirmación del informe | Valor en el informe | Dónde y cómo verificarla | Valor que encontré | ¿Coincide? | Diferencia o nota |
|---|---|---:|---|---:|:---:|---|
| 1 | Crédito directo del sistema financiero en Piura, fin de 2020 y fin de 2024 (millones de S/; hallazgo 4 y validaciones) | 8 630 y 9 049 | Tabla web del BCRP, serie RD16184DA: https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/RD16184DA/html/2020/2024/ | 8630 y 9049 | Sí| |
| 2 | Inflación de Lima entre diciembre de 2020 y diciembre de 2024 (%; hallazgo 3) | 21,51 | Tabla web del BCRP, índice PN38705PM: https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN38705PM/html/2020-12/2024-12/ · leer el índice de dic-2020 y el de dic-2024 y calcular (dic-2024 ÷ dic-2020 − 1) × 100 | 21,51| Sí |  |
| 3 | Pobreza monetaria nacional 2024 (%; validaciones) | 27,58 | Cifra oficial del INEI (informe técnico «Evolución de la pobreza monetaria 2015-2024»), citada en la prensa: https://forbes.pe/economia-y-finanzas/2025-05-09/pobreza-monetaria-se-redujo-en-2024-esto-es-lo-que-hay-que-saber/ | 27,6 | Sí| Se espera 27,6 % (diferencia de redondeo) |
| 4 | Pobreza monetaria de Piura 2024 (%; hallazgo 4) | 31,86 | Cifra por departamento del INEI en la prensa (https://www.bloomberglinea.com/latinoamerica/peru/los-departamentos-mas-golpeados-por-la-pobreza-monetaria-en-peru-segun-el-inei/) o la referencia del curso (Sesión 16): https://github.com/d2cml-ai/Data-Science-Python/blob/main/sessions/16-skills-enaho/referencias/pobreza_departamento_2024.csv | 31.9 | Sí| La referencia del curso dice 31,9 fue redondeado |
| 5 | Crédito por habitante en Piura 2024 (S/ por persona; hallazgo 4) | 4 550,6 | Con calculadora: 9 049,12 millones (fila 1) × 1 000 000 ÷ 1 988 570 personas (población de Piura que estima la ENAHO, en `salidas/indicadores.csv`, fila de Piura, columna `poblacion`) | 4 550,5 | Sí| Se redondeó de 4 550,506 142.605|

## Diferencias ya conocidas

- **Pobreza nacional:** el informe calcula 27,58 % con el método del INEI (sumaria con `factor07 × mieperho`); el
  INEI publica 27,6 %. Es redondeo. Con residentes y `facpob07` se obtiene 27,53 %, también dentro de la tolerancia
  de 0,1 puntos del issue.
- **Pobreza extrema:** la prensa cita 5,5 % y, en algunos medios, 5,7 %; la ENAHO procesada da 5,50 %.
- **Correlación de Spearman:** el informe da −0,604 porque la skill usa la pobreza redondeada a 2 decimales de
  `salidas/indicadores.csv`, que deja empatados a Lima y Ucayali (27,07 %). Sin redondear, el cálculo independiente
  de la evaluación (`evaluacion/respuestas_esperadas.py`) da −0,609. La conclusión no cambia.
- **Tabla web del BCRP en el informe:** el agente contrastó Lima, Piura y el total con una URL de solo esas tres
  series (lo aclara el propio informe), no con el enlace de las 26.
