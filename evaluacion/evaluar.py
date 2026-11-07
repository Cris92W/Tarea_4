"""Evaluación: las 10 preguntas de evaluacion/preguntas.csv, sin y con MCP/Skills, contra la respuesta esperada.

    uv run evaluacion/evaluar.py --trabajo ../evaluacion_trabajo              # los dos modos, Sonnet, 3 a la vez
    uv run evaluacion/evaluar.py --trabajo ../evaluacion_trabajo --modos A --ids b1 e1

Modo A, sin MCP ni Skills: Claude Code solo con búsqueda web (WebSearch y WebFetch). Sin terminal, sin archivos, sin
MCP y sin Skills, en una carpeta vacía: no puede leer cifras ya calculadas.
Modo B, con MCP y Skills: lo mismo más el servidor MCP bcrp, las Skills del proyecto y la terminal y los archivos que
ellas necesitan, en una copia limpia del proyecto sin salidas ni la referencia de la Sesión 16.
En los dos: el mismo modelo, la misma instrucción, cada pregunta en una sesión nueva (--no-session-persistence) y
sin la memoria automática de Claude Code. Cada ejecución queda en evidencias_ia/evaluacion/ (JSONL y Markdown).
Escribe evaluacion/resultados.csv y las tablas de evaluacion/comparacion.md.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from espacio_limpio import espacio_limpio  # noqa: E402
from registro import a_markdown, ocultar, ocultar_todo  # noqa: E402

INSTRUCCION = ("Responde con la cifra que pide la pregunta en «valor» y, si pide dos cifras, la segunda en «valor_2», "
               "en la unidad que pide. Si no puedes obtenerla con certeza, pon null: no estimes. En «fuente» di de "
               "dónde sale cada cifra y en «interpretacion» explica la respuesta en una o dos frases.\n\n")
ESQUEMA = {"type": "object", "required": ["valor", "fuente", "interpretacion"],
           "properties": {"valor": {"type": ["number", "null"]}, "valor_2": {"type": ["number", "null"]},
                          "fuente": {"type": "string"}, "interpretacion": {"type": "string"}}}
MODOS = {
    "A": {"descripcion": "sin MCP ni Skills: solo búsqueda web (WebSearch, WebFetch), en una carpeta vacía",
          "herramientas": "WebSearch,WebFetch", "permitidas": "WebSearch,WebFetch", "mcp": False, "skills": False},
    "B": {"descripcion": "con el MCP bcrp y las Skills del proyecto, más la terminal, los archivos y la búsqueda web, "
                         "en una copia limpia del proyecto",
          "herramientas": "Skill,Bash,Read,Glob,Grep,Write,WebSearch,WebFetch",
          "permitidas": "mcp__bcrp,Skill,Bash,Read,Glob,Grep,Write,WebSearch,WebFetch", "mcp": True, "skills": True},
}
CAUSAL = re.compile(r"\b(causa|provoca|genera|determina|reduce la pobreza|aumenta la pobreza)\b", re.I)
NEGACION = re.compile(r"\b(no|sin)\b[^.]{0,40}\b(causa|causal|causalidad)", re.I)


def preparar(modo, pregunta_id, trabajo):
    carpeta = trabajo / f"{modo}_{pregunta_id}_{time.strftime('%H%M%S')}"     # nueva cada vez: nunca se borra nada
    if modo == "A":
        carpeta.mkdir(parents=True, exist_ok=False)                   # vacía: nada que leer
    else:
        espacio_limpio(carpeta, referencias=False)
    return carpeta


def preguntar(fila, modo, modelo, trabajo):
    m = MODOS[modo]
    carpeta = preparar(modo, fila.id, trabajo)
    cmd = ["claude", "-p", INSTRUCCION + fila.pregunta, "--model", modelo, "--output-format", "stream-json",
           "--verbose", "--no-session-persistence", "--settings", json.dumps({"autoMemoryEnabled": False}),
           "--json-schema", json.dumps(ESQUEMA), "--strict-mcp-config", "--tools", m["herramientas"],
           "--allowedTools", m["permitidas"]]
    if m["mcp"]:
        cmd += ["--mcp-config", str(carpeta / ".mcp.json")]
    if not m["skills"]:
        cmd += ["--disallowedTools", "Skill"]
    entorno = os.environ | {"UV_PROJECT_ENVIRONMENT": str(RAIZ / ".venv")}
    inicio = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=carpeta, timeout=1500,
                              env=entorno)
        salida, error = proc.stdout, (proc.stderr[-500:] if proc.returncode else "")
    except subprocess.TimeoutExpired as e:
        salida, error = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), \
            "se agotó el tiempo (25 min)"
    segundos = round(time.time() - inicio, 1)
    lineas = []
    for linea in salida.splitlines():
        try:
            lineas.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
    # Registro de la ejecución como evidencia
    base = RAIZ / "evidencias_ia" / "evaluacion" / f"{fila.id}_{modo}"
    base.parent.mkdir(parents=True, exist_ok=True)
    cabecera = {"type": "registro", "prompt": INSTRUCCION + fila.pregunta, "comando": cmd[:2] + ["<pregunta>"] + cmd[3:],
                "cwd": f"{modo}_{fila.id} ({m['descripcion']})", "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "segundos": segundos, "codigo_salida": 0 if not error else 1, "stderr": error}
    base.with_suffix(".jsonl").write_text("\n".join(json.dumps(ocultar_todo(x), ensure_ascii=False)
                                                    for x in [cabecera] + lineas) + "\n", encoding="utf-8")
    a_markdown(base.with_suffix(".jsonl"))
    herramientas = []
    for x in lineas:
        if x.get("type") == "assistant":
            for b in x.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    herramientas.append(f"Skill:{b['input'].get('skill')}" if b["name"] == "Skill" else b["name"])
    fin = next((x for x in lineas if x.get("type") == "result"), {})
    r = fin.get("structured_output") or {}
    return {"valor": r.get("valor"), "valor_2": r.get("valor_2"), "fuente": ocultar(str(r.get("fuente", ""))),
            "interpretacion": ocultar(str(r.get("interpretacion", fin.get("result", "")))),
            "herramientas": ";".join(dict.fromkeys(herramientas)), "n_llamadas": len(herramientas),
            "uso_mcp": any(h.startswith("mcp__bcrp") for h in herramientas),
            "uso_skills": any(h.startswith("Skill:") for h in herramientas),
            "segundos": segundos, "turnos": fin.get("num_turns"),
            "error": error or ("sin respuesta estructurada" if not r else "")}


def dentro(valor, esperado, tolerancia):
    return valor is not None and not pd.isna(esperado) and abs(float(valor) - float(esperado)) <= float(tolerancia)


def calificar(fila, r):
    if r["valor"] is None and r["valor_2"] is None:
        return "sin respuesta"
    ok1 = dentro(r["valor"], fila.respuesta_esperada, fila.tolerancia)
    if fila.id == "c1":
        ok2 = dentro(r["valor_2"], fila.respuesta_esperada_2, fila.tolerancia_2)
        return "correcta" if ok1 and ok2 else "parcial" if ok1 or ok2 else "incorrecta"
    if fila.id == "c2":
        texto = r["interpretacion"]
        interpreta = bool(re.search(r"negativ|invers", texto, re.I)) and not (
            CAUSAL.search(texto) and not NEGACION.search(texto))
        return "correcta" if ok1 and interpreta else "parcial" if ok1 or interpreta else "incorrecta"
    return "correcta" if ok1 else "incorrecta"


def comparacion(res, modelo):
    """Las tablas de comparacion.md, calculadas de resultados.csv (el análisis escrito va debajo)."""
    orden = ["correcta", "parcial", "incorrecta", "sin respuesta"]
    t = res.groupby("modo").resultado.value_counts().unstack(fill_value=0).reindex(columns=orden, fill_value=0)
    t["segundos promedio"] = res.groupby("modo").segundos.mean().round(1)
    t["usó el MCP"] = res.groupby("modo").uso_mcp.sum()
    t["usó Skills"] = res.groupby("modo").uso_skills.sum()
    por_tipo = res.pivot_table(index="tipo", columns="modo", values="resultado",
                               aggfunc=lambda s: f"{(s == 'correcta').sum()} de {len(s)}")
    detalle = res.pivot(index="id", columns="modo", values="resultado")
    tiempos = res.pivot(index="id", columns="modo", values="segundos")
    detalle = detalle.join(tiempos, rsuffix=" (s)")
    return t, por_tipo, detalle


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--trabajo", type=Path, required=True, help="carpeta nueva fuera del repositorio para las copias")
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--ids", nargs="*")
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--paralelo", type=int, default=3)
    a = p.parse_args()
    preguntas = pd.read_csv(AQUI / "preguntas.csv")
    if a.ids:
        preguntas = preguntas[preguntas.id.isin(a.ids)]
    casos = [(f, m) for f in preguntas.itertuples() for m in a.modos]
    print(f"{len(casos)} ejecuciones de claude -p con {a.modelo}, {a.paralelo} a la vez…", flush=True)
    with ThreadPoolExecutor(a.paralelo) as ex:
        respuestas = list(ex.map(lambda c: preguntar(c[0], c[1], a.modelo, a.trabajo), casos))
    filas = []
    for (f, m), r in zip(casos, respuestas):
        filas.append({"id": f.id, "tipo": f.tipo, "modo": m, "pregunta": f.pregunta,
                      "respuesta_esperada": f.respuesta_esperada, "respuesta_esperada_2": f.respuesta_esperada_2,
                      **r, "resultado": calificar(f, r)})
    nuevos = pd.DataFrame(filas)
    destino = AQUI / "resultados.csv"
    if destino.exists() and a.ids:                                   # re-correr algunas: se reemplazan esas filas
        previos = pd.read_csv(destino)
        nuevos = pd.concat([previos[~(previos.id.isin(a.ids) & previos.modo.isin(a.modos))], nuevos])
    nuevos = nuevos.sort_values(["id", "modo"]).reset_index(drop=True)
    nuevos.to_csv(destino, index=False, encoding="utf-8")
    t, por_tipo, detalle = comparacion(nuevos, a.modelo)
    print("\n" + t.to_string() + "\n\n" + por_tipo.to_string() + "\n\n" + detalle.to_string())
