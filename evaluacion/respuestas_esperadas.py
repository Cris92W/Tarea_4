"""Arma evaluacion/preguntas.csv: las 10 preguntas de la evaluación con su respuesta esperada y su tolerancia.

    uv run evaluacion/respuestas_esperadas.py

Las respuestas esperadas NO salen del agente ni del código que se evalúa (mcp/server.py y las Skills):
- BCRP: cada cifra se pide directo a la API pública del BCRP con httpx.
- ENAHO: las cifras publicadas (27.6, 39.3, 5.5 %) son las de referencia del issue #201 y de la Sesión 16, y se
  recalculan aparte leyendo el .dta del INEI con pandas; las que no se publican (Piura rural) salen de ese cálculo.
- Combinadas: el mismo cálculo independiente une la API del BCRP con el .dta del INEI.
Se generan y se guardan antes de correr la evaluación, y no se cambian después de ver los resultados.
"""
import sys
import time
import zipfile
from pathlib import Path

import httpx
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
CREDITO_DEPARTAMENTOS = [f"RD{c}DA" for c in range(16127, 16200, 3)]    # «(total)» de Amazonas (01) a Ucayali (25)


def bcrp(codigos, desde, hasta):
    """La API responde una página HTML si recibe muchos pedidos seguidos: se espera y se reintenta."""
    for espera in (0, 3, 6, 12, 24):
        time.sleep(espera)
        try:
            return httpx.get(f"{API}/{'-'.join(codigos)}/json/{desde}/{hasta}", timeout=90, follow_redirects=True).json()
        except (httpx.HTTPError, ValueError):
            continue
    raise SystemExit(f"El BCRP no respondió con datos para {codigos} tras 5 intentos.")


def un_valor(codigo, periodo):
    return float(bcrp([codigo], periodo, periodo)["periods"][0]["values"][0])


def sumaria():
    with zipfile.ZipFile(RAIZ / "datos/enaho/966-Modulo34.zip") as z, z.open("966-Modulo34/sumaria-2024.dta") as f:
        s = pd.read_stata(f, convert_categoricals=False, columns=["ubigeo", "estrato", "mieperho", "pobreza", "factor07"])
    s["ccdd"] = s.ubigeo.astype(str).str[:2]
    s["peso"] = s.factor07.astype("float64") * s.mieperho
    s["pobre"] = s.pobreza <= 2
    s["extremo"] = s.pobreza == 1
    return s


def tasa(s, columna="pobre"):
    return 100 * (s.peso * s[columna]).sum() / s.peso.sum()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = sumaria()
    piura = s[s.ccdd == "20"]
    credito_piura = un_valor("RD16184DA", 2024)

    # Crédito de los 25 departamentos directo de la API; la API devuelve las series ordenadas por código
    r = bcrp(sorted(CREDITO_DEPARTAMENTOS), 2024, 2024)
    nombres = [x["name"] for x in r["config"]["series"]]
    credito = pd.Series([float(v) for v in r["periods"][0]["values"]], index=[f"{i:02d}" for i in range(1, 26)])
    assert "Amazonas" in nombres[0] and "Ucayali" in nombres[-1] and len(credito) == 25
    por_dep = s.groupby("ccdd").apply(lambda g: pd.Series({"pobreza": tasa(g), "poblacion": g.peso.sum()}))
    por_dep["credito_pc"] = credito * 1e6 / por_dep.poblacion
    rho = por_dep.pobreza.rank().corr(por_dep.credito_pc.rank())       # Spearman: Pearson sobre los rangos

    filas = [
        ("b1", "bcrp", "¿Cuál fue la inflación interanual (variación del IPC en 12 meses) de Lima Metropolitana en "
         "diciembre de 2024, en %?", un_valor("PN01273PM", "2024-12"), "%", 0.05, None, "", None,
         "valor dentro de la tolerancia", "BCRP, serie PN01273PM, dic-2024 (API directa)"),
        ("b2", "bcrp", "¿Cuál era la tasa de referencia de la política monetaria del BCRP en diciembre de 2024, en %?",
         un_valor("PD04722MM", "2024-12"), "%", 0.01, None, "", None, "valor dentro de la tolerancia",
         "BCRP, serie PD04722MM, dic-2024 (API directa)"),
        ("b3", "bcrp", "¿Cuánto creció el PBI real del Perú en 2024 según el BCRP, en %?", un_valor("PM04923AA", 2024),
         "%", 0.05, None, "", None, "valor dentro de la tolerancia", "BCRP, serie PM04923AA, 2024 (API directa)"),
        ("b4", "bcrp", "¿A cuánto ascendía el crédito directo del sistema financiero al sector privado en el "
         "departamento de Piura a fin de 2024, en millones de soles?", credito_piura, "millones de S/",
         round(credito_piura * 0.01, 2), None, "", None, "valor dentro de 1 %",
         "BCRP, serie RD16184DA, 2024 (API directa)"),
        ("e1", "enaho", "Según la ENAHO 2024 del INEI, ¿qué porcentaje de la población del Perú estaba en situación "
         "de pobreza monetaria en 2024?", 27.6, "%", 0.1, None, "", None, "valor dentro de la tolerancia",
         f"Cifra oficial del INEI (referencia del issue #201); recálculo independiente con la sumaria: {tasa(s):.2f}"),
        ("e2", "enaho", "Según la ENAHO 2024 del INEI, ¿cuál fue la tasa de pobreza monetaria del área rural del Perú "
         "en 2024, en %?", 39.3, "%", 0.15, None, "", None, "valor dentro de la tolerancia",
         f"Cifra oficial del INEI (referencia del issue #201); recálculo independiente: {tasa(s[s.estrato >= 6]):.2f}"),
        ("e3", "enaho", "Según los microdatos de la ENAHO 2024 del INEI, ¿cuál fue la tasa de pobreza monetaria del "
         "área rural del departamento de Piura en 2024, en %?", round(tasa(piura[piura.estrato >= 6]), 2), "%", 0.5,
         None, "", None, "valor dentro de la tolerancia (el INEI no la publica: hay que calcularla)",
         "Cálculo independiente con la sumaria del INEI: ubigeo 20…, estrato >= 6, factor07 × mieperho"),
        ("e4", "enaho", "Según la ENAHO 2024 del INEI, ¿qué porcentaje de la población del Perú estaba en pobreza "
         "extrema en 2024?", 5.5, "%", 0.1, None, "", None, "valor dentro de la tolerancia",
         f"Cifra de referencia de la Sesión 16; recálculo independiente: {tasa(s, 'extremo'):.2f}"),
        ("c1", "combinada", "En 2024, ¿cuál fue la tasa de pobreza monetaria del departamento de Piura según la ENAHO "
         "(en %) y cuánto crédito directo del sistema financiero por habitante tenía Piura a fin de ese año según el "
         "BCRP (en soles por persona), usando como población la que estima la ENAHO 2024?",
         round(tasa(piura), 2), "%", 0.15, round(credito_piura * 1e6 / piura.peso.sum(), 1), "S/ por persona",
         round(credito_piura * 1e6 / piura.peso.sum() * 0.02, 1),
         "correcta si los dos valores están en tolerancia; parcial si solo uno",
         "BCRP RD16184DA (API directa) ÷ población de Piura de la sumaria; pobreza de la sumaria (método del INEI)"),
        ("c2", "combinada", "Entre los 25 departamentos del Perú, ¿cuál es la correlación de rangos de Spearman entre "
         "la tasa de pobreza monetaria de 2024 (ENAHO, método del INEI) y el crédito directo del sistema financiero "
         "por habitante a fin de 2024 (BCRP, con la población que estima la ENAHO)? Interpreta el signo.",
         round(rho, 3), "coeficiente", 0.05, None, "", None,
         "correcta si el coeficiente está en tolerancia y la interpretación dice que la asociación es negativa sin "
         "afirmar causalidad; parcial si solo una de las dos",
         "25 series RD161xxDA (API directa) ÷ población de la sumaria; Spearman con pandas"),
    ]
    columnas = ["id", "tipo", "pregunta", "respuesta_esperada", "unidad", "tolerancia", "respuesta_esperada_2",
                "unidad_2", "tolerancia_2", "criterio", "verificacion"]
    tabla = pd.DataFrame(filas, columns=columnas)
    tabla["respuesta_esperada"] = tabla.respuesta_esperada.round(4)
    destino = RAIZ / "evaluacion" / "preguntas.csv"
    tabla.to_csv(destino, index=False, encoding="utf-8")
    print(tabla[["id", "tipo", "respuesta_esperada", "tolerancia", "respuesta_esperada_2", "tolerancia_2"]].to_string(index=False))
    print(f"\nGuardado en {destino.relative_to(RAIZ).as_posix()}")
