"""Aplica la revisión manual a resultados.csv y escribe las tablas de la comparación.

    uv run evaluacion/calificar.py

La calificación automática de evaluar.py queda en «resultado_automatico». Si revision_manual.csv corrige un caso
(por ejemplo, una interpretación que cumple el criterio con otras palabras), «resultado» toma ese valor y
«revision» guarda el motivo. Sin revisión, «resultado» es el automático. Escribe evaluacion/tablas.md.
"""
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
ORDEN = ["correcta", "parcial", "incorrecta", "sin respuesta"]


def tabla_md(df):
    columnas = [str(c) for c in df.columns]
    filas = ["| " + " | ".join([df.index.name or ""] + columnas) + " |", "|" + "---|" * (len(columnas) + 1)]
    filas += ["| " + " | ".join([str(i)] + [str(v) for v in fila]) + " |" for i, fila in df.astype(object).iterrows()]
    return "\n".join(filas)


def herramientas(texto):
    """StructuredOutput es como Claude Code entrega la respuesta en JSON, no una herramienta usada."""
    usadas = [h for h in str(texto).split(";") if h and h != "StructuredOutput" and h != "nan"]
    return ", ".join(usadas) or "ninguna"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = pd.read_csv(AQUI / "resultados.csv")
    if "resultado_automatico" not in r.columns:
        r["resultado_automatico"] = r.resultado
    revision = pd.read_csv(AQUI / "revision_manual.csv")
    r = r.drop(columns=[c for c in ("revision",) if c in r.columns]).merge(
        revision.rename(columns={"resultado": "resultado_revisado", "motivo": "revision"}), on=["id", "modo"], how="left")
    r["resultado"] = r.resultado_revisado.fillna(r.resultado_automatico)
    r = r.drop(columns="resultado_revisado")
    r.to_csv(AQUI / "resultados.csv", index=False, encoding="utf-8")

    resumen = r.groupby("modo").resultado.value_counts().unstack(fill_value=0).reindex(columns=ORDEN, fill_value=0)
    resumen["segundos promedio"] = r.groupby("modo").segundos.mean().round(1)
    resumen["usó el MCP"] = r.groupby("modo").uso_mcp.sum()
    resumen["usó Skills"] = r.groupby("modo").uso_skills.sum()
    por_tipo = r.pivot_table(index="tipo", columns="modo", values="resultado",
                             aggfunc=lambda s: f"{(s == 'correcta').sum()} de {len(s)}")
    detalle = r.pivot(index="id", columns="modo", values="resultado").add_prefix("resultado ")
    detalle = detalle.join(r.pivot(index="id", columns="modo", values="segundos").add_prefix("segundos "))
    detalle = detalle.join(r.assign(herramientas=r.herramientas.map(herramientas))
                           .pivot(index="id", columns="modo", values="herramientas").add_prefix("herramientas "))
    texto = ["# Tablas de la evaluación", "", "Generadas por `uv run evaluacion/calificar.py` a partir de "
             "[`resultados.csv`](resultados.csv).", "", "## Resumen por modo", "", tabla_md(resumen), "",
             "## Correctas por tipo de pregunta", "", tabla_md(por_tipo), "", "## Detalle por pregunta", "",
             tabla_md(detalle), ""]
    (AQUI / "tablas.md").write_text("\n".join(texto), encoding="utf-8")
    print("\n".join(texto))
