# Referencia de la ENAHO 2024 para limpiando-enaho

Las etiquetas vienen de los propios `.dta` del INEI (`sumaria-2024.dta` y `enaho01-2024-200.dta`).

## Archivos

| Módulo | Archivo en el zip | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|---|
| 34, sumaria | `966-Modulo34/sumaria-2024.dta` | hogar | 33 691 | `conglome`, `vivienda`, `hogar` | `factor07` |
| 02, miembros | `966-Modulo02/enaho01-2024-200.dta` | persona | 117 721 | las tres + `codperso` | `facpob07` |

El zip del módulo 34 también trae `sumaria-2024-12g.dta` (gasto en 12 grupos); no se usa. Los diccionarios del INEI
están en los mismos zip (`Diccionario2024.pdf`, `FichaTecnica.pdf`).

## Llaves

Vienen como texto y con ceros a la izquierda; nunca se leen como números. Anchos: `conglome` 6, `vivienda` 3,
`hogar` 2, `codperso` 2, `ubigeo` 6. El departamento es `ubigeo[:2]` (`ccdd`): 01 Amazonas … 15 Lima, 07 Callao
(separado de Lima) … 25 Ucayali. Es el mismo código que `FIRST_IDDP` en el GeoJSON del curso.

## Variables de la base limpia (`salidas/personas_2024.parquet`)

| Variable | Origen | Significado |
|---|---|---|
| `conglome`, `vivienda`, `hogar`, `codperso` | 02 | Llaves (texto) |
| `ubigeo`, `ccdd`, `departamento` | 02 | Ubicación; `ccdd = ubigeo[:2]`; nombre con tildes |
| `dominio`, `dominio_nombre` | 34 | 1 costa norte, 2 costa centro, 3 costa sur, 4 sierra norte, 5 sierra centro, 6 sierra sur, 7 selva, 8 Lima Metropolitana (provincia de Lima y Callao) |
| `estrato` | 34 | 1: 500 000 hab. o más; 2: 100 000 a 499 999; 3: 50 000 a 99 999; 4: 20 000 a 49 999; 5: 2 000 a 19 999; 6: 500 a 1 999; 7: AER compuesto; 8: AER simple |
| `area` | construida | «Urbana» si `estrato <= 5`; «Rural» si `estrato >= 6` |
| `p203` | 02 | Parentesco con el jefe: 1 jefe(a), 2 cónyuge, 3 hijo(a), 4 yerno/nuera, 5 nieto(a), 6 padres/suegros, 7 otros parientes, 8 trabajador del hogar, 9 pensionista, 10 otros no parientes, 11 hermano(a), 0 panel |
| `sexo` | 02, `p207` | «Hombre» (1) o «Mujer» (2) |
| `sexo_jefe` | 02, `p207` del jefe (`p203 == 1`) | Sexo de quien encabeza el hogar; sale del módulo completo, porque el jefe puede estar ausente |
| `edad`, `grupo_edad` | 02, `p208a` | Años cumplidos; grupos 0 a 14, 15 a 29, 30 a 44, 45 a 64, 65 y más |
| `mieperho` | 34 | Total de miembros del hogar según el INEI; coincide con el número de residentes habituales en el 94.7 % de los hogares |
| `pobreza` | 34 | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre`, `pobre_extremo` | construidas | `pobreza <= 2` y `pobreza == 1` |
| `gasto_pc_mensual` | 34 | `gashog2d / (12 × mieperho)`: gasto total bruto per cápita al mes, en soles |
| `linea`, `linpe` | 34 | Línea de pobreza total y extrema (alimentaria), per cápita al mes |
| `factor07` | 34 | Factor de expansión del hogar (proyecciones del CPV 2007) |
| `facpob07` | 02 | Factor de expansión de la persona |

Residente habitual: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))`. `p204`: ¿es miembro del hogar?;
`p205`: ¿estuvo ausente 30 días o más?; `p206`: ¿está presente 30 días o más? (1 sí, 2 no).

## Cómo se pondera

| Pregunta | Base | Peso | Ejemplo |
|---|---|---|---|
| Pobreza de un territorio o de un tipo de hogar | `hogares_2024.parquet` | `factor07 × mieperho` | Perú 27.58 %, Piura 31.86 % |
| Pobreza según un rasgo de la persona | `personas_2024.parquet` | `facpob07` | Mujeres 27.68 %, 0 a 14 años 37.52 % |

El método de hogares es el del INEI y reproduce las cifras oficiales y la referencia de la Sesión 16 (diferencia
máxima de 0.05 puntos en los 25 departamentos). Con residentes y `facpob07` el total nacional da 27.53 %: cambian
quiénes se cuentan (los residentes habituales no siempre son los `mieperho` del hogar) y el factor de expansión.

## Validaciones (en `salidas/validacion.txt`)

| Verificación | Esperado | Tipo |
|---|---|---|
| Llaves de ancho fijo, solo dígitos; hogares y personas sin duplicados | 0 duplicados | esencial |
| Residentes habituales | 108 664 de 117 721 | esencial |
| Un jefe por hogar; unión `m:1` sin perder ni duplicar filas | 0 | esencial |
| Códigos `ubigeo[:2]` | 25 (01 a 25) | esencial |
| Factores positivos; población con personas y con hogares a menos de 1 % | sí | esencial |
| Pobreza nacional (método del INEI y con `facpob07`) | 27.6 % ± 0.1 pp | esencial |
| Urbana, rural, Lima Metropolitana, extrema | 24.8, 39.3, 28.2, 5.5 % | control |
| `pobreza` concuerda con gasto per cápita < línea | 99 % o más | control |

## Trampas conocidas

- La columna del año llega como `aÑo`; se normaliza a `anio`.
- `p204`, `p205`, `p206`, `p207` y `p208a` vienen como decimales con nulos: comparar con `== 1`, no con texto.
- `factor07` y `facpob07` vienen en float32: se convierten a float64 antes de sumar.
- Lima Metropolitana (dominio 8) no es el departamento de Lima (15): reúne hogares del Callao (07) y de la provincia
  de Lima; Lima provincias cae en los dominios costa centro y sierra centro.
- Un promedio simple da 25.61 % de pobreza: sin ponderar, la cifra está mal.
