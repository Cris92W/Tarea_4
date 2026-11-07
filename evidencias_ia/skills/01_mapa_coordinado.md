# Registro: 01_mapa_coordinado

- **Fecha:** 2026-11-07T12:31:25 · **duración total:** 99.2 s · **carpeta:** `ws2`
- **Comando:** `claude -p <pregunta> --model sonnet --output-format stream-json --verbose --no-session-persistence --settings {"autoMemoryEnabled": false} --strict-mcp-config --tools Skill,Bash,Read,Glob,Grep --allowedTools Bash,Read,Glob,Grep,Skill`
- **Modelo:** claude-sonnet-5-5 · **Claude Code** 2.1.319 · **servidores MCP:** ninguno
- **Herramientas disponibles:** Bash, Glob, Grep, Read, Skill
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho

## Pregunta

Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.

## Ejecución

**Herramienta:** `Skill → `mapeando-enaho``

```json
{
 "skill": "mapeando-enaho"
}
```

<details><summary>Resultado</summary>

```
Launching skill: mapeando-enaho
```

</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls salidas datos referencias 2>&1; cat salidas/validacion.txt 2>&1 | head -30"
}
```

<details><summary>Resultado</summary>

```
ls: cannot access 'salidas': No such file or directory
ls: cannot access 'referencias': No such file or directory
datos:
bcrp
enaho
geo
referencias
cat: salidas/validacion.txt: No such file or directory
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws2
```

</details>

**Claude:** No existe la base limpia, así que uso primero limpiando-enaho.

**Herramienta:** `Skill → `limpiando-enaho``

```json
{
 "skill": "limpiando-enaho"
}
```

<details><summary>Resultado</summary>

```
Launching skill: limpiando-enaho
```

</details>

**Herramienta:** `Bash`

```json
{
 "command": "ls datos/enaho; ls .claude/skills/limpiando-enaho/scripts; [ -f datos/enaho/966-Modulo34.zip ] && [ -f datos/enaho/966-Modulo02.zip ] || uv run .claude/skills/limpiando-enaho/scripts/descargar.py"
}
```

<details><summary>Resultado</summary>

```
966-Modulo02.zip
966-Modulo34.zip
consultar.py
descargar.py
limpiar.py
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws2
```

</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/limpiando-enaho/scripts/limpiar.py 2>&1 | tail -30; cat salidas/validacion.txt"
}
```

<details><summary>Resultado</summary>

```
Sumaria:  datos/enaho/966-Modulo34.zip → 966-Modulo34/sumaria-2024.dta (33 691 hogares)
Personas: datos/enaho/966-Modulo02.zip → 966-Modulo02/enaho01-2024-200.dta (117 721 filas)
Esencial: si falla, la base no se guarda. Control: se informa, pero no detiene el proceso.

[APROBADA] (esencial) Llaves con sus ceros iniciales (conglome 6, vivienda 3, hogar 2, codperso 2, ubigeo 6 dígitos): todas de ancho fijo y solo dígitos
[APROBADA] (esencial) Llaves de hogar únicas en la sumaria (conglome, vivienda, hogar): 33 691 hogares, 0 duplicados | esperado: 0 duplicados
[APROBADA] (esencial) Llaves de persona únicas en el módulo 02 (+ codperso): 117 721 filas, 0 duplicados | esperado: 0 duplicados
[APROBADA] (esencial) Residentes habituales: ((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1)): 108 664 de 117 721 filas | esperado: 108 664
[APROBADA] (esencial) Cada hogar de la sumaria tiene un solo jefe o jefa en el módulo 02 (merge 1:1): 0 hogares sin jefe | esperado: 0
[APROBADA] (esencial) Unión personas-hogares con merge(validate='m:1') sin duplicar ni perder filas: 108 664 filas antes, 108 664 después, 0 personas sin hogar | esperado: iguales y 0
[APROBADA] (control ) El ubigeo de cada persona coincide con el de su hogar: 0 diferencias | esperado: 0
[APROBADA] (esencial) Códigos territoriales ubigeo[:2]: los 25 departamentos del INEI, cada uno con nombre: 25 códigos (01 a 25) en personas y en hogares | esperado: 25 (01 a 25)
[APROBADA] (esencial) Cada residente tie
[… 5548 caracteres más en el .jsonl]
```

</details>

**Claude:** La validación aprobó las 19 verificaciones. Ahora hago el mapa.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/mapeando-enaho/scripts/mapear.py 2>&1 | tail -50"
}
```

<details><summary>Resultado</summary>

```
Unión por código: 25 de 25 departamentos con dato; nombres que difieren tras quitar tildes: 0.
Comparación con la referencia de la Sesión 16: 25 departamentos, diferencia máxima 0.05 puntos; 25 de 25 a 0.1 puntos o menos. Detalle en salidas/comparacion_mapa.csv
Mapa: mapas/pobreza_departamento_2024.png y mapas/pobreza_departamento_2024.csv
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws2
```

</details>

**Herramienta:** `Bash`

```json
{
 "command": "cat mapas/pobreza_departamento_2024.csv | head -30"
}
```

<details><summary>Resultado</summary>

```
ccdd,departamento,pobreza_pct,clase,poblacion,pobres,n_hogares
01,Amazonas,25.75,20 a 30 %,442355.0,113901.0,1243
02,Áncash,22.77,20 a 30 %,1212494.0,276140.0,1393
03,Apurímac,23.96,20 a 30 %,494189.0,118401.0,913
04,Arequipa,15.78,10 a 20 %,1421684.0,224404.0,1506
05,Ayacucho,32.76,30 a 40 %,775447.0,254062.0,1160
06,Cajamarca,45.01,40 a 50 %,1554586.0,699671.0,1469
07,Callao,33.86,30 a 40 %,1142618.0,386889.0,1027
08,Cusco,18.54,10 a 20 %,1409467.0,261334.0,1230
09,Huancavelica,33.4,30 a 40 %,543103.0,181415.0,1042
10,Huánuco,38.96,30 a 40 %,926653.0,361048.0,1244
11,Ica,6.01,0 a 10 %,854203.0,51373.0,1500
12,Junín,18.5,10 a 20 %,1450149.0,268269.0,1506
13,La Libertad,30.19,30 a 40 %,2080789.0,628197.0,1509
14,Lambayeque,14.04,10 a 20 %,1349731.0,189511.0,1302
15,Lima,27.07,20 a 30 %,11279909.0,3053352.0,4544
16,Loreto,42.97,40 a 50 %,1129071.0,485191.0,1359
17,Madre de Dios,11.15,10 a 20 %,165992.0,18504.0,603
18,Moquegua,10.97,10 a 20 %,198386.0,21759.0,963
19,Pasco,38.97,30 a 40 %,327776.0,127741.0,865
20,Piura,31.86,30 a 40 %,1988570.0,633578.0,1611
21,Puno,39.94,30 a 40 %,1586886.0,633772.0,1123
22,San Martín,22.02,20 a 30 %,947446.0,208642.0,1347
23,Tacna,23.99,20 a 30 %,380755.0,91339.0,1271
24,Tumbes,26.9,20 a 30 %,261959.0,70470.0,842
25,Ucayali,27.07,20 a 30 %,558484.0,151182.0,1119
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6
[… 36 caracteres más en el .jsonl]
```

</details>

**Herramienta:** `Read`

```json
{
 "file_path": "~\\AppData\\Local\\Temp\\claude\\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\\scratchpad\\t4\\ws2\\mapas\\pobreza_departamento_2024.png"
}
```

<details><summary>Resultado</summary>

```
{"type": "image", "source": {"type": "base64", "data": "iVBORw0KGgoAAAANSUhEUgAABfAAAAdYCAYAAAB/6ujdAAAAOnRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjExLjIsIGh0dHBzOi8vbWF0cGxvdGxpYi5vcmcvgI3uAAAAAAlwSFlzAAAewgAAHsIBbtB1PgABAABJREFUeJzs3QV0XMXXAPChAi3F3d3d3Snu7g5/3N3d+XB3d3etYMUpULTQ4tSg0AKlynfugw3JZpNGNtlN8vud05N0k+zOzpN9786dOxOMGTP67wQAAAAAAJSVdqVuAAAAAAAAUJ0APgAAAAAAlCEBfAAAAAAAKEMC+AAAAAAAUIYE8AEAAAAAoAwJ4AMAAAAAQBkSwAcAAAAAgDIkgA8AAAAAAGVIAB8AAAAAAMqQAD4AAAAAAJQhAXwAAAAAAChDAvgAAAAAAFCGBPABAAAAAKAMCeADAAAAAEAZEsAHAAAAAIAyJIAPAAAAAABlSAAfAAAAAADKkAA+AAAAAACUIQF8AAAAAAAoQwL4AAAAAABQhgTwAQAAAACgDAngAwAAAABAGRLABwAAAACAMiSADwAAAAAAZUgAHwAAAAAAypAAPgAAAAAAlCEBfAAAAAAAKEMC+AAAAAAAUIYE8AEAAAAAoAwJ4AMAAAAAQBkSwAcAAAAAgDIkgA8AAAAAAGVIAB8AAAAAAMqQAD4AAAAAAJQhAXwAAAAAAChDAvgAAAAAAFCGBPABAAAAAKAMCeADAAAAAEAZEsAHAAAAAIAyJIAPAAAAAABlSAAfAAAAAADKkAA+AAAAAACUIQF8AAAAAAAoQwL4AAAAAABQhgTwAQAAAACgDAngAwAAAABAGRLABwAAAACAMtSh1A2g5fvqq37p22+/rfJY586d0gorrFCyNtF2xL4X+2BlE07YMa288solaxMAtFVDhgxJ/fv3T7POOmuaYYYZSt0cAABo8Vp9AL979x7VHpttttnS3HPPVZL2tEa33357uvTSS6s8Nttss6aPPvqoZG2i7XjwwYfS6aefXuWxqaaaKvXvXzWoX65++eWX9NNPP2VfJ5poojTttNNlx0/79u2L+jpjxoxJP/74Yxo4cGBq1659mmGG6dPMM8+cmsoff/yR+vbtm/7888803XTTpXnmmafOf9uvX//0zTffVPx/2mmnSYssskgTtbTl+fjjj9OgQYOrPDbxxJ3T8ssvX7I2tQW//DI0ffDBB1Uem2yySdPSSy9d49+8/37v9Ouvv9brdZZaask0+eSTp2Jx7Le9/fTnn4ekn3/+OY0dOzZ17jxxmm66adOMM85Y9M+VQk4//Yx02WWXZa89wQQTpD322CNdfPH/Zd8DAAAN0+oD+Jtvvnm1xw477LB0+umnlaQ9AF9++WW67bbb06OPPlpt9kro0qVL2mOP3dPZZ5/d6M76/PPP0+WXX5GefPLJ
[… 383750 caracteres más en el .jsonl]
```

</details>

**Claude:** Hice el mapa coroplético de la pobreza monetaria por departamento con la ENAHO 2024.

- **Mapa:** `mapas/pobreza_departamento_2024.png`
- **Datos del mapa (CSV):** `mapas/pobreza_departamento_2024.csv`
- **Comparación con la Sesión 16:** `salidas/comparacion_mapa.csv`

**Rango:** Ica tiene la menor pobreza, con 6.0 %. Cajamarca tiene la mayor, con 45.0 %. Después de Cajamarca vienen Loreto (43.0 %) y Puno (39.9 %). El total nacional es 27.6 %.

**Cómo salió:**
- **Validación:** las 19 verificaciones de la limpieza aprobaron, incluida la pobreza nacional de 27.58 %, que coincide con la oficial.
- **Unión con el mapa:** se hizo por código (`ubigeo[:2]` con `FIRST_IDDP`) y calzaron los 25 departamentos. Lima y Callao quedaron separados.
- **Comparación con la Sesión 16:** la diferencia máxima departamento por departamento es 0.05 puntos. Los 25 quedan a 0.1 puntos o menos.
- **Escala:** son 5 clases de 10 puntos en un solo tono de azul. La leyenda indica cuántos departamentos hay en cada clase: 1, 6, 8, 8 y 2.
- **Ponderación:** `factor07 × mieperho`, el método del INEI.

**Fuente:** INEI, ENAHO 2024, módulos 34 y 02.

En el PNG, los nombres de Lambayeque, Moquegua y Huancavelica se montan un poco sobre los bordes. Se leen, pero si lo vas a presentar puedo ajustar esas etiquetas.

## Resultado final

Hice el mapa coroplético de la pobreza monetaria por departamento con la ENAHO 2024.

- **Mapa:** `mapas/pobreza_departamento_2024.png`
- **Datos del mapa (CSV):** `mapas/pobreza_departamento_2024.csv`
- **Comparación con la Sesión 16:** `salidas/comparacion_mapa.csv`

**Rango:** Ica tiene la menor pobreza, con 6.0 %. Cajamarca tiene la mayor, con 45.0 %. Después de Cajamarca vienen Loreto (43.0 %) y Puno (39.9 %). El total nacional es 27.6 %.

**Cómo salió:**
- **Validación:** las 19 verificaciones de la limpieza aprobaron, incluida la pobreza nacional de 27.58 %, que coincide con la oficial.
- **Unión con el mapa:** se hizo por código (`ubigeo[:2]` con `FIRST_IDDP`) y calzaron los 25 departamentos. Lima y Callao quedaron separados.
- **Comparación con la Sesión 16:** la diferencia máxima departamento por departamento es 0.05 puntos. Los 25 quedan a 0.1 puntos o menos.
- **Escala:** son 5 clases de 10 puntos en un solo tono de azul. La leyenda indica cuántos departamentos hay en cada clase: 1, 6, 8, 8 y 2.
- **Ponderación:** `factor07 × mieperho`, el método del INEI.

**Fuente:** INEI, ENAHO 2024, módulos 34 y 02.

En el PNG, los nombres de Lambayeque, Moquegua y Huancavelica se montan un poco sobre los bordes. Se leen, pero si lo vas a presentar puedo ajustar esas etiquetas.

- **Turnos:** 11 · **tiempo de la API:** 94.9 s · **error:** False

## Herramientas usadas

- `Bash`: 5
- `Skill:mapeando-enaho`: 1
- `Skill:limpiando-enaho`: 1
- `Read`: 1
