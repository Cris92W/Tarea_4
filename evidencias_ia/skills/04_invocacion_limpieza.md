# Registro: 04_invocacion_limpieza

- **Fecha:** 2026-11-07T12:35:11 · **duración total:** 23.0 s · **carpeta:** `ws5`
- **Comando:** `claude -p <pregunta> --model sonnet --output-format stream-json --verbose --no-session-persistence --settings {"autoMemoryEnabled": false} --strict-mcp-config --tools Skill,Bash,Read,Glob,Grep --allowedTools Bash,Read,Glob,Grep,Skill`
- **Modelo:** claude-sonnet-5-5 · **Claude Code** 2.1.319 · **servidores MCP:** ninguno
- **Herramientas disponibles:** Bash, Glob, Grep, Read, Skill
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho

## Pregunta

/limpiando-enaho

## Ejecución

**Claude:** Primero reviso qué archivos ya existen.

**Herramienta:** `Bash`

```json
{
 "command": "ls datos/enaho salidas 2>&1; ls .claude/skills/limpiando-enaho/scripts"
}
```

<details><summary>Resultado</summary>

```
ls: cannot access 'salidas': No such file or directory
datos/enaho:
966-Modulo02.zip
966-Modulo34.zip
consultar.py
descargar.py
limpiar.py
Shell cwd was reset to ~\AppData\Local\Temp\claude\C--Users-usuario-Documents-Diplomado-Ciencia-de-Datos-Python-1-Python-2-Python-Intermedio\a3e53fdd-9c69-46d6-a6a0-268a06ad4539\scratchpad\t4\ws5
```

</details>

**Claude:** Los zips ya están; falta la base limpia, así que corro el script de limpieza.

**Herramienta:** `Bash`

```json
{
 "command": "uv run .claude/skills/limpiando-enaho/scripts/limpiar.py 2>&1 | tail -40; echo ----; cat salidas/validacion.txt",
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
[… 5717 caracteres más en el .jsonl]
```

</details>

**Claude:** La limpieza de la ENAHO 2024 terminó sin errores. Pasaron las 19 validaciones, incluidas todas las esenciales, y ninguna falló.

**Qué se generó**
- `salidas/personas_2024.parquet`: 108 664 residentes habituales, con 25 columnas.
- `salidas/hogares_2024.parquet`: 33 691 hogares, con `peso_inei`.
- `salidas/indicadores.csv`: 45 filas de indicadores ponderados.
- `salidas/validacion.txt`: el detalle de cada verificación.

**Pobreza monetaria nacional 2024**

| Indicador | Método | Valor |
|---|---|---|
| Pobreza | Sumaria con `factor07 × mieperho` (método del INEI) | **27,58 %** |
| Pobreza | Residentes con `facpob07` | 27,53 % |
| Pobreza extrema | Método del INEI | 5,50 % |

- **Controles de contraste:** coinciden con las cifras oficiales de referencia.
  - Urbana: 24,81 %.
  - Rural: 39,30 %.
  - Lima Metropolitana: 28,21 %.
- **Sin ponderar:** el promedio simple da 25,61 %, así que la ponderación sí cambia la cifra.
- **Población expandida:** con personas suma 34 147 766 y con la sumaria 34 482 699, una diferencia menor al 1 %.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

Ya puedes pedirme cifras por departamento, área, sexo o edad, o pasar a las skills de gráficos y mapas.

## Resultado final

La limpieza de la ENAHO 2024 terminó sin errores. Pasaron las 19 validaciones, incluidas todas las esenciales, y ninguna falló.

**Qué se generó**
- `salidas/personas_2024.parquet`: 108 664 residentes habituales, con 25 columnas.
- `salidas/hogares_2024.parquet`: 33 691 hogares, con `peso_inei`.
- `salidas/indicadores.csv`: 45 filas de indicadores ponderados.
- `salidas/validacion.txt`: el detalle de cada verificación.

**Pobreza monetaria nacional 2024**

| Indicador | Método | Valor |
|---|---|---|
| Pobreza | Sumaria con `factor07 × mieperho` (método del INEI) | **27,58 %** |
| Pobreza | Residentes con `facpob07` | 27,53 % |
| Pobreza extrema | Método del INEI | 5,50 % |

- **Controles de contraste:** coinciden con las cifras oficiales de referencia.
  - Urbana: 24,81 %.
  - Rural: 39,30 %.
  - Lima Metropolitana: 28,21 %.
- **Sin ponderar:** el promedio simple da 25,61 %, así que la ponderación sí cambia la cifra.
- **Población expandida:** con personas suma 34 147 766 y con la sumaria 34 482 699, una diferencia menor al 1 %.

Fuente: INEI, ENAHO 2024, módulos 34 y 02.

Ya puedes pedirme cifras por departamento, área, sexo o edad, o pasar a las skills de gráficos y mapas.

- **Turnos:** 3 · **tiempo de la API:** 20.6 s · **error:** False

## Herramientas usadas

- `Bash`: 2
