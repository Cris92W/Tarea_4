---
name: mapeando-enaho
description: Hace el mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI, uniendo cada departamento por su código oficial (ubigeo[:2] con FIRST_IDDP), con las 25 unidades, Lima y Callao separados, y lo compara con la referencia de la Sesión 16. Úsala cuando pidan un mapa, un coroplético o la distribución territorial o geográfica de la pobreza por departamento o región.
---

# Mapear la pobreza de la ENAHO 2024 por departamento

1. Si no existe `salidas/hogares_2024.parquet` (o `salidas/personas_2024.parquet`), usa primero la skill
   **limpiando-enaho** y revisa su `salidas/validacion.txt`. Si la validación falló, no mapees: dilo.
2. Corre (con `--resaltar <departamento>` si piden destacar uno, p. ej. Piura):
   ```bash
   uv run .claude/skills/mapeando-enaho/scripts/mapear.py
   ```
   Si faltan el GeoJSON del curso o la referencia de la Sesión 16, el script los baja a `datos/`.
3. Si el script dice «UNIÓN FALLIDA», detente y explica qué códigos no calzaron. No unas por nombre.
4. Responde con la ruta del mapa y de su CSV, el rango (departamento con menor y mayor pobreza, del CSV) y la
   diferencia máxima con la referencia que imprime el script (también en `salidas/comparacion_mapa.csv`).

## Qué garantiza el script

- **Unión por código, nunca por nombre:** `ubigeo[:2]` de la ENAHO con `FIRST_IDDP` del GeoJSON, los dos como texto
  de dos dígitos, con `merge(validate="1:1")`. Exige 25 de 25 con dato y Lima (15) y Callao (07) separados.
- **Cifras:** pobreza monetaria ponderada con `factor07 × mieperho` (método del INEI), comparada departamento por
  departamento con `referencias/pobreza_departamento_2024.csv` de la Sesión 16.
- **Escala:** 5 clases iguales desde 0 % (0 a 10, …, 40 a 50 %) en un solo tono de azul, de claro a oscuro, validado
  con `validate_palette.py --ordinal`; nunca arcoíris. La leyenda dice la unidad (% de la población) y cuántos
  departamentos hay en cada clase.
- **Lectura:** cada departamento lleva su nombre y su cifra; Tumbes y Callao, que son pequeños, van al mar con una
  guía. Proyección equivalente de Albers para Sudamérica (ESRI:102033).
- **Salidas:** `mapas/pobreza_departamento_2024.png` (200 dpi), su CSV y `salidas/comparacion_mapa.csv`.
