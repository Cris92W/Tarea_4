---
name: cruzando-bcrp-enaho
description: Cruza un indicador departamental del BCRP (crédito, depósitos, gasto o inversión pública, afiliados al SPP) con la pobreza monetaria de la ENAHO 2024 por el código del INEI de cada departamento. Calcula el indicador por habitante, su variación nominal y real, la correlación de Spearman con la pobreza (con prueba de permutación) y los terciles de pobreza, y hace dos gráficos. Úsala cuando pregunten si un indicador económico de los departamentos se asocia con la pobreza, o cómo cambió según el nivel de pobreza.
---

# Cruzar el BCRP con la ENAHO por departamento

Las cifras del BCRP llegan por el MCP `bcrp` y las de la ENAHO por la skill `limpiando-enaho`. Este script solo las
une por código y hace las cuentas. Entre herramientas se pasan **archivos**, nunca cifras copiadas a mano.

## Pasos

1. Si no existe `salidas/indicadores.csv`, usa primero la skill **limpiando-enaho**.
2. Pide el indicador al MCP `bcrp`, con el año de la pobreza, un año base y `guardar=True`:
   `panel_departamental(indicador="credito directo", anio=2024, anio_base=2020, guardar=True)`. Anota el `archivo`
   que devuelve.
3. Para pasar a términos reales, busca un **índice** de precios (no su variación %) con `buscar_series`, por ejemplo
   «indice precios lima metropolitana indice», y guárdalo del cierre del año base al cierre del año final:
   `serie(codigo="PN38705PM", desde="2020-12", hasta="2024-12", guardar=True)`. Anota el `archivo`.
4. Corre:
   ```bash
   uv run .claude/skills/cruzando-bcrp-enaho/scripts/cruzar.py --panel <archivo del paso 2> --ipc <archivo del paso 3> --resaltar Piura
   ```
5. Toma las cifras de `salidas/cruce_<indicador>.json` y `.csv`, nunca de memoria. Si el script se detiene (faltan
   departamentos, datos o columnas), dilo y no completes a mano.

## Qué calcula

- **Por habitante:** el valor del BCRP (millones de S/ × 1 000 000) entre la población que estima la ENAHO
  (`factor07 × mieperho`).
- **Variación nominal y real:** la real es (valor final / valor base) / (índice final / índice base) − 1.
- **Asociación:** correlación de rangos de Spearman entre la pobreza y el indicador por habitante, con y sin Lima y
  Callao, con un valor p por permutación (20 000 repeticiones, semilla fija). También entre la pobreza y la variación real.
- **Terciles de pobreza:** medianas del indicador por habitante y de su variación real en cada tercil.

## Cómo interpretarlo

- Es una asociación entre departamentos, no una relación causal. Tampoco dice nada de los hogares: lo que pasa
  entre departamentos puede no pasar dentro de ellos (falacia ecológica).
- Con 25 departamentos, un valor p alto no prueba que no haya relación; dilo así.
- El BCRP publica el crédito por departamento con datos de la SBS. Lima concentra la mayor parte; parte de esa
  concentración puede deberse al criterio con que se asigna cada crédito a un departamento, que debe citarse como
  limitación y no darse por conocido.
- El índice de precios de Lima se usa para todos los departamentos: cambia el nivel de las variaciones reales, pero
  no el orden entre departamentos.

## Salidas

| Archivo | Qué es |
|---|---|
| `salidas/cruce_<indicador>.csv` y `.json` | La tabla por departamento y el resumen con sus fuentes |
| `figuras/bcrp_<indicador>_real_<base>_<año>.png` | La variación real por departamento (gráfico del BCRP), con el color del tercil de pobreza |
| `figuras/<indicador>_vs_pobreza_<año>.png` | El indicador por habitante frente a la pobreza, con los promedios nacionales |
