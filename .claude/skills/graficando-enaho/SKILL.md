---
name: graficando-enaho
description: Hace gráficos de la pobreza monetaria con la ENAHO 2024 del INEI, ponderados, con título que dice el hallazgo, unidades, año y fuente, y los guarda en figuras/. Úsala cuando pidan graficar, visualizar o comparar la pobreza entre áreas urbana y rural, entre mujeres y hombres o según quién encabeza el hogar, por grupos de edad, entre departamentos o regiones, o por dominio (costa, sierra, selva).
---

# Graficar la pobreza de la ENAHO 2024

1. Si no existe `salidas/personas_2024.parquet` o `salidas/hogares_2024.parquet`, usa primero la skill
   **limpiando-enaho** y revisa su `salidas/validacion.txt`. Si la validación falló, no grafiques: dilo.
2. Elige el tipo según el pedido:

   | Si piden… | Comando |
   |---|---|
   | urbana y rural, área de residencia | `--tipo area` |
   | sexo, mujeres y hombres, jefa o jefe de hogar | `--tipo sexo` |
   | edad, niños, jóvenes, adultos mayores | `--tipo edad` |
   | departamentos, regiones, ranking territorial | `--tipo departamento` (con `--resaltar Piura` si piden destacar uno) |
   | costa, sierra y selva, dominios geográficos | `--tipo dominio` |
   | todos los anteriores | `--tipo todos` |

3. Corre:
   ```bash
   uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo <tipo>
   ```
4. Responde con la ruta del PNG y de su CSV gemelo, y resume el hallazgo con las cifras de ese CSV, nunca de memoria.
   Si piden un gráfico que el script no hace, dilo y ofrece el más cercano; no hagas promedios simples por tu cuenta.

## Qué garantiza el script

- **Ponderación:** territorios y tipos de hogar con `factor07 × mieperho` (método del INEI); rasgos de la persona
  (sexo, edad) con `facpob07`. Cada gráfico lo dice en la nota.
- **Forma:** barras horizontales desde cero, ordenadas de mayor a menor (la edad va en su orden natural). El tramo
  oscuro es la pobreza extrema y la barra completa, la pobreza total. Una línea marca el total nacional.
- **Texto:** el título dice el hallazgo con cifras calculadas en el momento; el subtítulo dice qué se mide, la unidad
  (% de la población) y el año; la nota trae la fuente («INEI, ENAHO 2024, módulos 34 y 02») y el método.
- **Color:** un solo tono de azul, validado con `validate_palette.py --ordinal` (el tono claro contrasta 2.44:1 con el
  fondo); al resaltar un departamento, los demás pasan a gris.
- **Salidas:** `figuras/pobreza_<tipo>.png` a 200 dpi y `figuras/pobreza_<tipo>.csv` con las cifras graficadas.
