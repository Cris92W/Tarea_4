# Registro: 02_grafico_area

- **Fecha:** 2026-11-07T12:35:26 · **duración total:** 38.5 s · **carpeta:** `ws3`
- **Comando:** `claude -p <pregunta> --model sonnet --output-format stream-json --verbose --no-session-persistence --settings {"autoMemoryEnabled": false} --strict-mcp-config --tools Skill,Bash,Read,Glob,Grep --allowedTools Bash,Read,Glob,Grep,Skill`
- **Modelo:** claude-sonnet-5-5 · **Claude Code** 2.1.319 · **servidores MCP:** ninguno
- **Herramientas disponibles:** Bash, Glob, Grep, Read, Skill
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho

## Pregunta

Grafica la pobreza monetaria urbana y rural del Perú con la ENAHO 2024.

## Ejecución

**Herramienta:** `Skill → `graficando-enaho``

```json
{
 "skill": "graficando-enaho"
}
```

<details><summary>Resultado</summary>

```
Launching skill: graficando-enaho
```

</details>

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
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws3
```

</details>

**Claude:** Faltan los datos limpios, así que uso primero la skill limpiando-enaho.

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
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws3
```

</details>

**Claude:** Los zips ya están. Corro la limpieza.

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

**Claude:** Validación aprobada (19/19). Ahora el gráfico.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo area 2>&1 | tail -15; cat figuras/pobreza_area.csv"
}
```

<details><summary>Resultado</summary>

```
area: figuras/pobreza_area.png y figuras/pobreza_area.csv
categoria,pobreza_pct,pobreza_extrema_pct,poblacion,n_muestra
Urbana,24.81,3.14,27887511.4,22031
Rural,39.3,15.52,6595187.91,11660
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws3
```

</details>

**Claude:** Hice el gráfico de la pobreza monetaria urbana y rural con la ENAHO 2024.

- **Gráfico:** `figuras/pobreza_area.png`
- **Cifras graficadas:** `figuras/pobreza_area.csv`

| Área | Pobreza total | Pobreza extrema | Población representada |
|---|---|---|---|
| Urbana | 24.81 % | 3.14 % | 27.9 millones |
| Rural | 39.30 % | 15.52 % | 6.6 millones |

La pobreza rural supera a la urbana en 14.5 puntos porcentuales. La diferencia es mayor en pobreza extrema: en el campo es casi 5 veces la de las ciudades (15.52 % frente a 3.14 %).

Las cifras usan los factores de expansión según el método del INEI (`factor07 × mieperho`) y coinciden con las oficiales: 24.8 % urbana y 39.3 % rural. La fuente es INEI, ENAHO 2024, módulos 34 y 02. Como faltaban los datos limpios, los preparé antes de graficar, y las 19 validaciones salieron aprobadas.

## Resultado final

Hice el gráfico de la pobreza monetaria urbana y rural con la ENAHO 2024.

- **Gráfico:** `figuras/pobreza_area.png`
- **Cifras graficadas:** `figuras/pobreza_area.csv`

| Área | Pobreza total | Pobreza extrema | Población representada |
|---|---|---|---|
| Urbana | 24.81 % | 3.14 % | 27.9 millones |
| Rural | 39.30 % | 15.52 % | 6.6 millones |

La pobreza rural supera a la urbana en 14.5 puntos porcentuales. La diferencia es mayor en pobreza extrema: en el campo es casi 5 veces la de las ciudades (15.52 % frente a 3.14 %).

Las cifras usan los factores de expansión según el método del INEI (`factor07 × mieperho`) y coinciden con las oficiales: 24.8 % urbana y 39.3 % rural. La fuente es INEI, ENAHO 2024, módulos 34 y 02. Como faltaban los datos limpios, los preparé antes de graficar, y las 19 validaciones salieron aprobadas.

- **Turnos:** 9 · **tiempo de la API:** 36.2 s · **error:** False

## Herramientas usadas

- `Bash`: 4
- `Skill:graficando-enaho`: 1
- `Skill:limpiando-enaho`: 1
