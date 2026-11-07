# Registro: 03_pregunta_cusco

- **Fecha:** 2026-11-07T12:35:21 · **duración total:** 33.2 s · **carpeta:** `ws4`
- **Comando:** `claude -p <pregunta> --model sonnet --output-format stream-json --verbose --no-session-persistence --settings {"autoMemoryEnabled": false} --strict-mcp-config --tools Skill,Bash,Read,Glob,Grep --allowedTools Bash,Read,Glob,Grep,Skill`
- **Modelo:** claude-sonnet-5-5 · **Claude Code** 2.1.319 · **servidores MCP:** ninguno
- **Herramientas disponibles:** Bash, Glob, Grep, Read, Skill
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho

## Pregunta

¿Cuál fue la pobreza monetaria en Cusco en 2024 según la ENAHO?

## Ejecución

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
 "command": "ls datos/enaho salidas 2>&1 | head -30"
}
```

<details><summary>Resultado</summary>

```
ls: cannot access 'salidas': No such file or directory
datos/enaho:
966-Modulo02.zip
966-Modulo34.zip
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws4
```

</details>

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/limpiando-enaho/scripts/limpiar.py 2>&1 | tail -40; cat salidas/validacion.txt",
 "timeout": 600000
}
```

<details><summary>Resultado</summary>

```
VALIDACIÓN · ENAHO 2024 (INEI), módulos 34 (sumaria) y 02 (miembros del hogar)
Generado por .claude/skills/limpiando-enaho/scripts/limpiar.py el 2026-11-07 12:35
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
[APROBADA] (esencial) Códigos territoriales ubigeo[:2]: 
[… 5712 caracteres más en el .jsonl]
```

</details>

**Herramienta:** `Grep`

```json
{
 "pattern": "Cusco",
 "path": "salidas/indicadores.csv",
 "output_mode": "content"
}
```

**Herramienta:** `Bash`

```json
{
 "command": "head -1 salidas/indicadores.csv"
}
```

<details><summary>Resultado</summary>

```
nivel,codigo,categoria,metodo,pobreza_pct,pobreza_extrema_pct,pobreza_pct_facpob07,poblacion,pobres,n_hogares,n_personas,pobres_pct_del_total
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws4
```

</details>

<details><summary>Resultado</summary>

```
20:departamento,08,Cusco,hogares: factor07 × mieperho (INEI),18.54,2.1,18.54,1409467.0,261334.0,1230,3777,2.75
```

</details>

**Claude:** **La pobreza monetaria en Cusco en 2024 fue de 18,5 %**, según la ENAHO 2024.

| Indicador | Valor |
|---|---|
| Pobreza monetaria | 18,54 % |
| Pobreza extrema | 2,1 % |
| Población representada | unas 1 409 467 personas |
| Personas pobres | unas 261 334 |
| Peso en el total de pobres del país | 2,75 % |
| Muestra | 1 230 hogares y 3 777 personas |

- **Ponderación:** usé el método del INEI, que toma la sumaria con `factor07 × mieperho`. Con los residentes ponderados por `facpob07` sale el mismo valor (18,54 %).
- **Comparación:** la cifra queda por debajo de la nacional, que es 27,58 % con el mismo método.
- **Validación:** las 19 verificaciones de la base salieron aprobadas, incluida la pobreza nacional (27,58 %).
- **Muestra:** no es un grupo de muestra pequeña.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

## Resultado final

**La pobreza monetaria en Cusco en 2024 fue de 18,5 %**, según la ENAHO 2024.

| Indicador | Valor |
|---|---|
| Pobreza monetaria | 18,54 % |
| Pobreza extrema | 2,1 % |
| Población representada | unas 1 409 467 personas |
| Personas pobres | unas 261 334 |
| Peso en el total de pobres del país | 2,75 % |
| Muestra | 1 230 hogares y 3 777 personas |

- **Ponderación:** usé el método del INEI, que toma la sumaria con `factor07 × mieperho`. Con los residentes ponderados por `facpob07` sale el mismo valor (18,54 %).
- **Comparación:** la cifra queda por debajo de la nacional, que es 27,58 % con el mismo método.
- **Validación:** las 19 verificaciones de la base salieron aprobadas, incluida la pobreza nacional (27,58 %).
- **Muestra:** no es un grupo de muestra pequeña.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

- **Turnos:** 7 · **tiempo de la API:** 30.6 s · **error:** False

## Herramientas usadas

- `Bash`: 3
- `Skill:limpiando-enaho`: 1
- `Grep`: 1
