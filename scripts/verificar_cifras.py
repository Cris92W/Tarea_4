"""Recalcula las cifras clave del informe por un camino independiente, sin usar el servidor MCP ni las Skills.

    uv run scripts/verificar_cifras.py            # escribe informes/verificacion_automatica.md

BCRP: pide cada serie directamente a la API pública (httpx), sin el código de mcp/server.py.
ENAHO: lee la sumaria .dta del zip del INEI con pandas, sin el código de las Skills.
Cruce: recalcula el crédito por habitante y la correlación de Spearman con pandas (corr(method="spearman")), otra
implementación que la de la skill. Compara cada cifra con la que usó el informe y dice si coincide.
Complementa, no reemplaza, la verificación manual de informes/verificacion.md.
"""
import json
import sys
import time
import zipfile
from pathlib import Path

import httpx
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def bcrp(codigo, desde, hasta):
    """La API responde una página HTML si recibe muchos pedidos seguidos: se espera y se reintenta."""
    for espera in (0, 3, 6, 12, 24):
        time.sleep(espera)
        try:
            r = httpx.get(f"{API}/{codigo}/json/{desde}/{hasta}", timeout=60, follow_redirects=True)
            return [float(p["values"][0]) for p in r.json()["periods"]]
        except (httpx.HTTPError, ValueError):
            continue
    raise SystemExit(f"El BCRP no respondió con datos para {codigo} tras 5 intentos.")


def sumaria():
    with zipfile.ZipFile(RAIZ / "datos/enaho/966-Modulo34.zip") as z, z.open("966-Modulo34/sumaria-2024.dta") as f:
        s = pd.read_stata(f, convert_categoricals=False, columns=["ubigeo", "mieperho", "pobreza", "factor07"])
    s["peso"] = s.factor07.astype("float64") * s.mieperho
    return s


def tasa(s):
    return 100 * (s.peso * (s.pobreza <= 2)).sum() / s.peso.sum()


def num(x):
    return f"{x:,.3f}".replace(",", " ")


def fila(afirmacion, informe, independiente, tolerancia, como):
    ok = abs(informe - independiente) <= tolerancia
    return {"afirmacion": afirmacion, "informe": informe, "independiente": independiente,
            "diferencia": round(independiente - informe, 4), "tolerancia": tolerancia,
            "coincide": "sí" if ok else "NO", "como": como}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cruce = pd.read_csv(RAIZ / "salidas/cruce_credito_directo.csv", dtype={"ccdd": str})
    resumen = json.loads((RAIZ / "salidas/cruce_credito_directo.json").read_text(encoding="utf-8"))
    indicadores = pd.read_csv(RAIZ / "salidas/indicadores.csv", dtype={"codigo": str})
    piura = cruce[cruce.ccdd == "20"].iloc[0]
    s = sumaria()
    filas = [
        fila("Crédito directo en Piura a fin de 2024 (millones de S/)", piura.valor, bcrp("RD16184DA", 2024, 2024)[0],
             0.01, "API del BCRP, serie RD16184DA, año 2024"),
        fila("Crédito directo total del Perú a fin de 2024 (millones de S/)", resumen["nacional"]["total"],
             bcrp("RD16202DA", 2024, 2024)[0], 1.0, "API del BCRP, serie RD16202DA (total), frente a la suma de los 25"),
        fila("Inflación de Lima, dic-2020 a dic-2024 (%)", resumen["inflacion"]["inflacion_pct"],
             round((bcrp("PN38705PM", "2024-12", "2024-12")[0] / bcrp("PN38705PM", "2020-12", "2020-12")[0] - 1) * 100, 3),
             0.01, "API del BCRP, índice PN38705PM de diciembre de cada año"),
        fila("Pobreza monetaria nacional 2024 (%)", float(indicadores.query("nivel == 'nacional'").pobreza_pct.iloc[0]),
             round(tasa(s), 2), 0.01, "sumaria-2024.dta del INEI leída directo, factor07 × mieperho"),
        fila("Pobreza monetaria en Piura 2024 (%)", round(float(piura.pobreza_pct), 2),
             round(tasa(s[s.ubigeo.astype(str).str[:2] == "20"]), 2), 0.01, "la misma sumaria, ubigeo que empieza con 20"),
        fila("Crédito por habitante en Piura 2024 (S/)", round(float(piura.por_habitante), 1),
             round(bcrp("RD16184DA", 2024, 2024)[0] * 1e6 / s[s.ubigeo.astype(str).str[:2] == "20"].peso.sum(), 1), 0.5,
             "crédito de la API ÷ población de Piura de la sumaria"),
        fila("Spearman pobreza vs. crédito por habitante, 25 departamentos", resumen["spearman_pobreza_vs_por_habitante"]["rho"],
             round(cruce.pobreza_pct.rank().corr(cruce.por_habitante.rank()), 3), 0.001,
             "Pearson de pandas sobre los rangos (la definición de Spearman), de salidas/cruce_credito_directo.csv"),
    ]
    tabla = pd.DataFrame(filas)
    lineas = ["# Verificación automática e independiente de cifras del informe", "",
              "Generada con `uv run scripts/verificar_cifras.py`. Cada cifra se recalcula sin el servidor MCP ni las "
              "Skills: el BCRP directo de su API y la ENAHO directo del archivo del INEI. Complementa la verificación "
              "manual de [`verificacion.md`](verificacion.md).", "",
              "| Afirmación | Informe | Recalculado | Diferencia | ¿Coincide? | Cómo se recalculó |", "|---|---:|---:|---:|:---:|---|"]
    lineas += [f"| {f.afirmacion} | {num(f.informe)} | {num(f.independiente)} | {f.diferencia:+.4f} | {f.coincide} "
               f"| {f.como} |" for f in tabla.itertuples()]
    lineas += ["", f"Resultado: {int((tabla.coincide == 'sí').sum())} de {len(tabla)} cifras coinciden dentro de su "
               "tolerancia."]
    (RAIZ / "informes/verificacion_automatica.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
