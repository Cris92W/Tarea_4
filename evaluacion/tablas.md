# Tablas de la evaluación

Generadas por `uv run evaluacion/calificar.py` a partir de [`resultados.csv`](resultados.csv).

## Resumen por modo

| modo | correcta | parcial | incorrecta | sin respuesta | segundos promedio | usó el MCP | usó Skills |
|---|---|---|---|---|---|---|---|
| A | 6 | 0 | 2 | 2 | 26.9 | 0 | 0 |
| B | 10 | 0 | 0 | 0 | 20.6 | 6 | 4 |

## Correctas por tipo de pregunta

| tipo | A | B |
|---|---|---|
| bcrp | 2 de 4 | 4 de 4 |
| combinada | 1 de 2 | 2 de 2 |
| enaho | 3 de 4 | 4 de 4 |

## Detalle por pregunta

| id | resultado A | resultado B | segundos A | segundos B | herramientas A | herramientas B |
|---|---|---|---|---|---|---|
| b1 | correcta | correcta | 5.6 | 10.9 | ninguna | mcp__bcrp__serie |
| b2 | correcta | correcta | 5.6 | 12.3 | ninguna | mcp__bcrp__buscar_series, mcp__bcrp__serie |
| b3 | incorrecta | correcta | 20.3 | 14.2 | WebSearch | mcp__bcrp__buscar_series, mcp__bcrp__resumen, mcp__bcrp__serie |
| b4 | incorrecta | correcta | 39.4 | 11.1 | WebSearch, WebFetch | mcp__bcrp__panel_departamental |
| c1 | correcta | correcta | 86.4 | 25.9 | WebSearch, WebFetch | Skill:cruzando-bcrp-enaho, Bash, mcp__bcrp__panel_departamental |
| c2 | sin respuesta | correcta | 22.8 | 34.5 | WebSearch, WebFetch | Skill:cruzando-bcrp-enaho, Bash, mcp__bcrp__panel_departamental, mcp__bcrp__serie |
| e1 | correcta | correcta | 15.2 | 19.0 | WebSearch | WebSearch |
| e2 | correcta | correcta | 15.2 | 28.0 | WebSearch | WebSearch, WebFetch |
| e3 | sin respuesta | correcta | 38.9 | 25.1 | WebSearch, WebFetch | Skill:limpiando-enaho, Bash |
| e4 | correcta | correcta | 19.2 | 25.2 | WebSearch, WebFetch | Skill:limpiando-enaho, Bash |
