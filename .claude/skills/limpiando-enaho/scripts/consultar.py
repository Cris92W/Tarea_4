"""Calcula la pobreza ponderada de la ENAHO para cualquier grupo, a partir de la base que deja limpiar.py.

    uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por departamento
    uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por area --donde "departamento == 'Piura'"
    uv run .claude/skills/limpiando-enaho/scripts/consultar.py --por sexo grupo_edad --indicador pobre_extremo

Si el grupo y el filtro solo usan rasgos del hogar o del territorio (departamento, ccdd, area, dominio_nombre,
estrato, sexo_jefe), pondera los hogares de la sumaria con factor07 × mieperho, como el INEI. Si usan rasgos de la
persona (sexo, edad, grupo_edad, p203), pondera a los residentes habituales con facpob07. Siempre imprime el
método, la población representada y el tamaño de muestra, y marca los grupos con menos de 100 hogares en la muestra.
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

DEL_HOGAR = {"conglome", "vivienda", "hogar", "ubigeo", "ccdd", "departamento", "dominio", "dominio_nombre",
             "estrato", "area", "sexo_jefe", "mieperho", "pobreza", "pobre", "pobre_extremo", "gasto_pc_mensual",
             "linea", "linpe", "factor07"}
INDICADORES = {"pobre": "pobreza monetaria", "pobre_extremo": "pobreza extrema"}
MUESTRA_MINIMA = 100        # hogares encuestados; con menos, la cifra es poco precisa


def consultar(por, donde=None, indicador="pobre", salidas=Path("salidas"), anio=2024):
    personas_pq, hogares_pq = salidas / f"personas_{anio}.parquet", salidas / f"hogares_{anio}.parquet"
    if not personas_pq.exists() or not hogares_pq.exists():
        raise SystemExit(f"No existe {personas_pq.as_posix()}: corre primero la skill limpiando-enaho "
                         "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py).")
    usadas = set(por) | (set(re.findall(r"[A-Za-z_]\w*", donde)) if donde else set())
    personas = pd.read_parquet(personas_pq)
    desconocidas = {c for c in por if c not in personas.columns}
    if desconocidas:
        raise SystemExit(f"No existen las columnas {sorted(desconocidas)}. Hay: {sorted(personas.columns)}. "
                         "Revisa reference.md.")
    if usadas & set(personas.columns) <= DEL_HOGAR:
        df, peso, metodo = pd.read_parquet(hogares_pq), "peso_inei", "hogares de la sumaria con factor07 × mieperho (INEI)"
        unidad = "hogares"
    else:
        df, peso, metodo = personas, "facpob07", "residentes habituales con facpob07"
        unidad = "personas"
    if donde:
        df = df.query(donde)
        if df.empty:
            raise SystemExit(f"El filtro {donde!r} no deja ninguna fila.")
    if not por:
        df, por = df.assign(total="Perú"), ["total"]
    df = df.assign(_pond=df[peso].astype("float64"), _cumple=df[peso].astype("float64") * df[indicador])
    g = df.groupby(por, observed=True)
    afectados = "pobres" if indicador == "pobre" else "pobres_extremos"
    tabla = pd.DataFrame({"poblacion": g._pond.sum().round(0), afectados: g._cumple.sum().round(0),
                          "n_muestra": g.size(),
                          "n_hogares": df.drop_duplicates(por + ["conglome", "vivienda", "hogar"])
                                         .groupby(por, observed=True).size()})
    tabla.insert(0, f"{indicador}_pct", (100 * tabla[afectados] / tabla.poblacion).round(2))
    tabla["aviso"] = tabla.n_hogares.lt(MUESTRA_MINIMA).map({True: "muestra pequeña", False: ""})
    print(f"ENAHO {anio} (INEI), {INDICADORES[indicador]} en % de la población. Método: {metodo}.")
    if donde:
        print(f"Filtro: {donde}")
    print(f"Muestra: {len(df):,} {unidad}; n_muestra = {unidad} de la muestra en cada grupo.\n".replace(",", " "))
    print(tabla.to_string())
    return tabla


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--por", nargs="*", default=[], help="columnas para agrupar, p. ej. departamento area")
    p.add_argument("--donde", help="filtro de pandas, p. ej. \"departamento == 'Piura'\"")
    p.add_argument("--indicador", default="pobre", choices=list(INDICADORES))
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--csv", type=Path, help="además, guarda la tabla en este CSV")
    a = p.parse_args()
    resultado = consultar(a.por, a.donde, a.indicador, a.salidas)
    if a.csv:
        a.csv.parent.mkdir(parents=True, exist_ok=True)
        resultado.to_csv(a.csv, encoding="utf-8")
        print(f"\nGuardado en {a.csv.as_posix()}")
