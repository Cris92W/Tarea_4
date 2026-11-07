# Plan de análisis: «¿Hay menos crédito donde hay más pobreza?»

## Interpretación de la pregunta
- **Asociación**: correlación (Spearman, con prueba de permutación) entre la incidencia de pobreza monetaria 2024 por departamento (ENAHO 2024) y el crédito directo del sistema financiero por habitante. No se interpreta como causalidad.
- **Variación real 2020–2024**: variación del crédito directo deflactada con un índice de precios, comparada entre terciles de pobreza.
- Unidad de análisis: 25 departamentos (Lima y Callao separados), unidos por código INEI (`ubigeo[:2]` = `ccdd`).

## Datos y fuentes
| Dato | Fuente | Herramienta |
|---|---|---|
| Crédito directo por departamento 2020 y 2024 | BCRP (series departamentales) | MCP bcrp: `buscar_series`, `panel_departamental` (guardar=True) |
| Una cifra para verificar en tabla web | BCRP, `fuente_web` | MCP bcrp: `serie`/`resumen` |
| Pobreza monetaria 2024 (módulos 34 y 02) | INEI, ENAHO 2024 | Skill `limpiando-enaho` |
| Gráfico de pobreza por departamento | ENAHO | Skill `graficando-enaho` |
| Mapa departamental | ENAHO + GeoJSON | Skill `mapeando-enaho` |
| Cruce BCRP–ENAHO | archivos de salida | Skill `cruzando-bcrp-enaho` |

## Indicadores
1. Pobreza monetaria 2024 por departamento (ponderada con factores de expansión).
2. Crédito directo por habitante 2024.
3. Variación nominal y real 2020–2024 del crédito, por departamento.
4. Spearman (pobreza vs. crédito per cápita) y p-valor por permutación.
5. Promedio/mediana de variación real por tercil de pobreza.

## Gráficos
- Variación real del crédito por departamento (BCRP).
- Pobreza por departamento (ENAHO).
- Mapa coroplético de pobreza.
- Dispersión crédito per cápita vs. pobreza, resaltando Piura.

## Validaciones
- Pobreza nacional ENAHO vs. cifra oficial INEI (27.6 %).
- Mapa vs. referencia de la Sesión 16 (`datos/referencias/pobreza_departamento_2024.csv`).
- Una cifra del BCRP contra su tabla web (`fuente_web`).

## Reglas
Sin cálculos manuales: las cifras pasan entre herramientas como archivos; toda cifra del informe se verifica con comandos sobre los archivos. Si una herramienta falla, se documenta.
