"""Corre Claude Code sin interfaz (claude -p) y guarda la ejecución completa como evidencia, en JSONL y en Markdown.

    uv run scripts/registro.py correr evidencias_ia/mcp/02_panel_credito --mcp -- "¿Qué departamentos ...?"
    uv run scripts/registro.py correr evidencias_ia/skills/01_mapa --skills -- "Haz un mapa de la pobreza ..."
    uv run scripts/registro.py md evidencias_ia/mcp/02_panel_credito.jsonl       # vuelve a escribir el .md

El .jsonl es el registro crudo de `--output-format stream-json --verbose` (cada llamada a una herramienta y lo que
devolvió), con una primera línea propia que anota la pregunta y el comando. El .md es el mismo registro, legible.
En los dos se ocultan la ruta de la carpeta personal y los correos.

En Git Bash, un prompt que empieza con «/» (p. ej. /mcp__bcrp__informe) se convierte en una ruta de Windows:
córranlo con MSYS_NO_PATHCONV=1 delante, o desde PowerShell.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MAX_RESULTADO = 1500        # caracteres de cada resultado de herramienta que entran al .md


def ocultar(texto):
    """Quita la ruta de la carpeta personal (con / o con \\ y \\\\) y cualquier correo."""
    texto = re.sub(r"[A-Za-z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/)[^\\/\"'\n]+", "~", texto)
    return re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[correo oculto]", texto)


def comando(prompt, mcp=False, skills=False, modelo="sonnet", herramientas=None, permitidas=None):
    """El comando de claude -p. Sin --mcp no se carga ningún servidor MCP; sin --skills la herramienta Skill no existe."""
    cmd = ["claude", "-p", prompt, "--model", modelo, "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--settings", json.dumps({"autoMemoryEnabled": False}), "--strict-mcp-config"]
    if mcp:
        cmd += ["--mcp-config", str(RAIZ / ".mcp.json")]
    if herramientas is not None:
        cmd += ["--tools", herramientas]
    permitidas = list(permitidas or []) + (["mcp__bcrp"] if mcp else []) + (["Skill"] if skills else [])
    if permitidas:
        cmd += ["--allowedTools", ",".join(permitidas)]
    if not skills:
        cmd += ["--disallowedTools", "Skill"]
    return cmd


def correr(base, prompt, cwd=RAIZ, **opciones):
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    cmd = comando(prompt, **opciones)
    inicio = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd, timeout=1800)
    cabecera = {"type": "registro", "prompt": prompt, "comando": cmd[:2] + ["<pregunta>"] + cmd[3:],
                "cwd": Path(cwd).resolve().relative_to(RAIZ).as_posix() if Path(cwd).resolve().is_relative_to(RAIZ)
                else Path(cwd).name, "fecha": datetime.now().isoformat(timespec="seconds"),
                "segundos": round(time.time() - inicio, 1), "codigo_salida": proc.returncode,
                "stderr": proc.stderr[-2000:]}
    jsonl = base.with_suffix(".jsonl")
    jsonl.write_text(ocultar(json.dumps(cabecera, ensure_ascii=False) + "\n" + proc.stdout), encoding="utf-8")
    md = a_markdown(jsonl)
    print(f"{jsonl.name}: {cabecera['segundos']} s, salida {proc.returncode}; {md}")
    return jsonl


def _bloques(mensaje):
    contenido = mensaje.get("content", [])
    return [{"type": "text", "text": contenido}] if isinstance(contenido, str) else contenido


def _texto_resultado(bloque):
    c = bloque.get("content")
    if isinstance(c, list):
        c = "\n".join(x.get("text", json.dumps(x, ensure_ascii=False)) for x in c)
    c = str(c)
    return c if len(c) <= MAX_RESULTADO else c[:MAX_RESULTADO] + f"\n[… {len(c) - MAX_RESULTADO} caracteres más en el .jsonl]"


def a_markdown(jsonl):
    """Escribe el .md de un registro y devuelve un resumen de las herramientas usadas."""
    jsonl = Path(jsonl)
    lineas = [json.loads(x) for x in jsonl.read_text(encoding="utf-8").splitlines() if x.strip()]
    cab = next((x for x in lineas if x.get("type") == "registro"), {})
    init = next((x for x in lineas if x.get("type") == "system" and x.get("subtype") == "init"), {})
    fin = next((x for x in lineas if x.get("type") == "result"), {})
    usadas = Counter()
    md = [f"# Registro: {jsonl.stem}", ""]
    if cab:
        md += [f"- **Fecha:** {cab['fecha']} · **duración total:** {cab['segundos']} s · **carpeta:** `{cab['cwd']}`",
               f"- **Comando:** `{' '.join(cab['comando'])}`"]
    if init:
        mcp = ", ".join(f"{s['name']} ({s['status']})" for s in init.get("mcp_servers", [])) or "ninguno"
        md += [f"- **Modelo:** {init.get('model')} · **Claude Code** {init.get('claude_code_version')} · "
               f"**servidores MCP:** {mcp}",
               f"- **Herramientas disponibles:** {', '.join(init.get('tools', [])) or 'ninguna'}"]
        prompts = [s for s in init.get("slash_commands", []) if s.startswith("mcp__")]
        if prompts:
            md.append(f"- **Prompts MCP disponibles como comandos:** {', '.join('/' + s for s in prompts)}")
        propias = [s for s in init.get("skills", []) if s.endswith("-enaho")]
        if propias:
            md.append(f"- **Skills del proyecto disponibles:** {', '.join(propias)}")
    if cab:
        md += ["", "## Pregunta", "", cab["prompt"], ""]
    md += ["## Ejecución", ""]
    for x in lineas:
        if x.get("type") not in ("assistant", "user"):
            continue
        for b in _bloques(x.get("message", {})):
            if b.get("type") == "text" and b["text"].strip() and x["type"] == "assistant":
                md += [f"**Claude:** {b['text'].strip()}", ""]
            elif b.get("type") == "tool_use":
                nombre = b["name"] + (f" → `{b['input'].get('skill')}`" if b["name"] == "Skill" else "")
                usadas[b["name"] if b["name"] != "Skill" else f"Skill:{b['input'].get('skill')}"] += 1
                md += [f"**Herramienta:** `{nombre}`", "", "```json",
                       json.dumps(b["input"], ensure_ascii=False, indent=1), "```", ""]
            elif b.get("type") == "tool_result":
                error = " (error)" if b.get("is_error") else ""
                md += [f"<details><summary>Resultado{error}</summary>", "", "```", _texto_resultado(b), "```",
                       "", "</details>", ""]
    if fin:
        md += ["## Resultado final", "", str(fin.get("result", "")).strip(), "",
               f"- **Turnos:** {fin.get('num_turns')} · **tiempo de la API:** "
               f"{round((fin.get('duration_ms') or 0) / 1000, 1)} s · **error:** {fin.get('is_error')}"]
    md += ["", "## Herramientas usadas", ""]
    md += [f"- `{k}`: {v}" for k, v in usadas.most_common()] or ["- ninguna"]
    salida = jsonl.with_suffix(".md")
    salida.write_text(ocultar("\n".join(md)) + "\n", encoding="utf-8")
    return dict(usadas)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="accion", required=True)
    c = sub.add_parser("correr", help="corre claude -p y guarda el registro")
    c.add_argument("base", help="ruta del registro sin extensión, p. ej. evidencias_ia/mcp/01_inflacion")
    c.add_argument("prompt")
    c.add_argument("--mcp", action="store_true", help="carga el servidor bcrp de .mcp.json")
    c.add_argument("--skills", action="store_true", help="permite las Skills del proyecto")
    c.add_argument("--modelo", default="sonnet")
    c.add_argument("--herramientas", help="lista para --tools; '' deja solo las del MCP")
    c.add_argument("--permitidas", default="", help="herramientas extra que no piden permiso, separadas por comas")
    c.add_argument("--cwd", default=str(RAIZ))
    m = sub.add_parser("md", help="vuelve a escribir el .md de un registro")
    m.add_argument("jsonl", nargs="+")
    a = p.parse_args()
    if a.accion == "correr":
        correr(a.base, a.prompt, cwd=a.cwd, mcp=a.mcp, skills=a.skills, modelo=a.modelo,
               herramientas=a.herramientas, permitidas=[x for x in a.permitidas.split(",") if x])
    else:
        for j in a.jsonl:
            print(j, a_markdown(j))
    sys.exit(0)
