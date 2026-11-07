# Registro: 05_invocacion_graficos

- **Fecha:** 2026-11-07T12:35:23 · **duración total:** 35.5 s · **carpeta:** `ws6`
- **Comando:** `claude -p <pregunta> --model sonnet --output-format stream-json --verbose --no-session-persistence --settings {"autoMemoryEnabled": false} --strict-mcp-config --tools Skill,Bash,Read,Glob,Grep --allowedTools Bash,Read,Glob,Grep,Skill`
- **Modelo:** claude-sonnet-5-5 · **Claude Code** 2.1.319 · **servidores MCP:** ninguno
- **Herramientas disponibles:** Bash, Glob, Grep, Read, Skill
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho

## Pregunta

/graficando-enaho edad

## Ejecución

**Herramienta:** `Bash`

```json
{
 "command": "ls salidas figuras 2>&1; cat salidas/validacion.txt 2>&1 | head -30"
}
```

<details><summary>Resultado</summary>

```
ls: cannot access 'salidas': No such file or directory
ls: cannot access 'figuras': No such file or directory
cat: salidas/validacion.txt: No such file or directory
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws6
```

</details>

**Claude:** Faltan los parquet, así que primero toca la skill limpiando-enaho.

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
 "command": "ls datos/enaho 2>&1; ls .claude/skills/limpiando-enaho/scripts"
}
```

<details><summary>Resultado</summary>

```
966-Modulo02.zip
966-Modulo34.zip
consultar.py
descargar.py
limpiar.py
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws6
```

</details>

**Claude:** Los zips ya están; corro la limpieza.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/limpiando-enaho/scripts/limpiar.py 2>&1 | tail -30; cat salidas/validacion.txt",
 "timeout": 600000
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

**Claude:** La validación pasó (19 aprobadas, 0 fallidas). Ahora hago el gráfico.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo edad 2>&1 | tail -15; cat figuras/pobreza_edad.csv",
 "timeout": 300000
}
```

<details><summary>Resultado</summary>

```
edad: figuras/pobreza_edad.png y figuras/pobreza_edad.csv
categoria,pobreza_pct,pobreza_extrema_pct,poblacion,n_muestra
0 a 14 años,37.52,8.59,7941993.71,26489
15 a 29 años,25.97,4.5,7512400.33,23122
30 a 44 años,27.87,5.59,6689118.84,20648
45 a 64 años,21.15,3.61,7803731.04,24735
65 y más años,22.74,4.81,4200521.87,13670
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws6
```

</details>

**Claude:** Hice el gráfico de pobreza por grupos de edad. La limpieza de la ENAHO 2024 pasó antes de graficar: 19 validaciones aprobadas y 0 fallidas.

- **Gráfico:** `figuras/pobreza_edad.png`
- **Cifras graficadas:** `figuras/pobreza_edad.csv`

| Grupo de edad | Pobreza (%) | Pobreza extrema (%) |
|---|---|---|
| 0 a 14 años | 37.52 | 8.59 |
| 15 a 29 años | 25.97 | 4.50 |
| 30 a 44 años | 27.87 | 5.59 |
| 45 a 64 años | 21.15 | 3.61 |
| 65 y más años | 22.74 | 4.81 |

**Hallazgo:** la pobreza afecta sobre todo a niñas y niños. El 37.5 % de quienes tienen 0 a 14 años es pobre, y el 8.6 % lo es en extremo. Ambas cifras son las más altas de todos los grupos. La pobreza más baja está entre los 45 y 64 años, con 21.2 %. Los mayores de 65 años están en 22.7 %.

La cifra nacional es 27.5 % con los residentes ponderados por `facpob07`, el factor que usa el script para sexo y edad. Esa ponderación es la que corresponde a los rasgos de la persona.

Fuente: INEI, ENAHO 2024, módulos 34 y 02. No vi la imagen: solo confirmé que el script la generó. Las cifras de arriba salen del CSV.

## Resultado final

Hice el gráfico de pobreza por grupos de edad. La limpieza de la ENAHO 2024 pasó antes de graficar: 19 validaciones aprobadas y 0 fallidas.

- **Gráfico:** `figuras/pobreza_edad.png`
- **Cifras graficadas:** `figuras/pobreza_edad.csv`

| Grupo de edad | Pobreza (%) | Pobreza extrema (%) |
|---|---|---|
| 0 a 14 años | 37.52 | 8.59 |
| 15 a 29 años | 25.97 | 4.50 |
| 30 a 44 años | 27.87 | 5.59 |
| 45 a 64 años | 21.15 | 3.61 |
| 65 y más años | 22.74 | 4.81 |

**Hallazgo:** la pobreza afecta sobre todo a niñas y niños. El 37.5 % de quienes tienen 0 a 14 años es pobre, y el 8.6 % lo es en extremo. Ambas cifras son las más altas de todos los grupos. La pobreza más baja está entre los 45 y 64 años, con 21.2 %. Los mayores de 65 años están en 22.7 %.

La cifra nacional es 27.5 % con los residentes ponderados por `facpob07`, el factor que usa el script para sexo y edad. Esa ponderación es la que corresponde a los rasgos de la persona.

Fuente: INEI, ENAHO 2024, módulos 34 y 02. No vi la imagen: solo confirmé que el script la generó. Las cifras de arriba salen del CSV.

- **Turnos:** 7 · **tiempo de la API:** 32.5 s · **error:** False

## Herramientas usadas

- `Bash`: 4
- `Skill:limpiando-enaho`: 1
