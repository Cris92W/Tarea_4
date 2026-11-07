---
name: limpiando-enaho
description: Limpia, une y valida los módulos 34 (sumaria) y 02 (miembros del hogar) de la ENAHO 2024 del INEI y arma la base de residentes habituales con pobreza monetaria, departamento, área y factores de expansión. Úsala cuando pidan limpiar, unir o validar la ENAHO, o cuando pregunten por la pobreza o la pobreza extrema del Perú en 2024: nacional, de un departamento, urbana o rural, por dominio, por sexo, por edad o según quién encabeza el hogar. Las skills graficando-enaho y mapeando-enaho la necesitan antes.
---

# Limpiar y consultar la ENAHO 2024

Las cifras salen de los scripts. No estimes ni escribas cifras de memoria, y no promedies sin ponderar.

## Pasos

1. Si faltan `datos/enaho/966-Modulo34.zip` o `datos/enaho/966-Modulo02.zip`, bájalos (966 = ENAHO 2024):
   ```bash
   uv run .claude/skills/limpiando-enaho/scripts/descargar.py
   ```
2. Si no existe `salidas/personas_2024.parquet`, corre exactamente:
   ```bash
   uv run .claude/skills/limpiando-enaho/scripts/limpiar.py
   ```
   El script lee los `.dta` sin convertir categorías y con las llaves como texto, normaliza los nombres, filtra a
   los residentes habituales, une personas y hogares con `merge(validate="m:1")`, construye los indicadores y valida.
3. Lee `salidas/validacion.txt`. Si el script terminó con error o alguna validación **esencial** dice FALLIDA,
   **detente** y cuéntale al usuario cuál falló y por qué. No sigas con cifras ni las ajustes a la referencia.
4. Para responder, busca primero en `salidas/indicadores.csv`: Perú, área, 8 dominios, 25 departamentos, sexo del
   jefe del hogar, sexo y grupo de edad, con la pobreza, la pobreza extrema, la población representada y los
   pobres. Para otro grupo o un cruce, usa `consultar.py` (abajo).
5. Cita siempre el año, el método de ponderación de la cifra (columna `metodo`) y la fuente: «INEI, ENAHO 2024,
   módulos 34 y 02». Si un grupo tiene «muestra pequeña», dilo.
6. Antes de usar una variable que no ves en la base, lee [reference.md](reference.md).

Solo está configurada la ENAHO 2024. Si piden otro año, dilo en vez de usar 2024.

## Consultas con consultar.py

```bash
uv run .claude/skills/limpiando-enaho/scripts/consultar.py                                   # Perú
uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento area          # cruce
uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por area --donde "departamento == 'Piura'"
uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por grupo_edad --indicador pobre_extremo
```

El script elige la ponderación correcta: si el grupo es del hogar o del territorio, la sumaria con
`factor07 × mieperho` (el método del INEI, que reproduce las cifras oficiales); si es un rasgo de la persona
(sexo, edad), los residentes con `facpob07`.

## Salidas

| Archivo | Qué es |
|---|---|
| `salidas/personas_2024.parquet` | Una fila por residente habitual (108 664) con su hogar, territorio, sexo, edad, pobreza y factores |
| `salidas/hogares_2024.parquet` | Una fila por hogar (33 691) con `peso_inei = factor07 × mieperho` |
| `salidas/validacion.txt` | Cada verificación con APROBADA o FALLIDA, lo obtenido y lo esperado |
| `salidas/indicadores.csv` | Los indicadores ponderados que usan las otras skills |
