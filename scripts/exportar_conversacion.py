"""Exporta una sesión de Claude Code (el .jsonl que guarda en ~/.claude/projects/) a Markdown y JSON, por fases.

    uv run scripts/exportar_conversacion.py <sesion.jsonl> \
        --fase "mcp|Planificación y Parte 1: servidor MCP|" \
        --fase "skills|Parte 2: Skills de la ENAHO|avanza la parte 2"

Cada --fase es «carpeta|título|texto»: la fase empieza en el primer mensaje del usuario que contiene ese texto (vacío
= desde el inicio) y termina donde empieza la siguiente. Escribe evidencias_ia/<carpeta>/00_conversacion.md (legible)
y 00_conversacion.json (cada mensaje, herramienta y resultado completos).

Es la «Opción B» del issue #201: la exportación del historial. Incluye cada mensaje del usuario, cada respuesta de
Claude y cada herramienta con su resultado. No incluye el razonamiento interno del modelo ni los mensajes internos
de Claude Code. Oculta los datos personales: rutas y nombre de usuario de la carpeta personal, correos, las notas de
memoria del asistente (hablan de otras tareas) y los comentarios de otros estudiantes en el issue. Con
--ocultar <archivo> oculta además cada término de ese archivo (p. ej. nombres de terceros); ese archivo no se sube.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PERU = timezone(timedelta(hours=-5))
MAX_RESULTADO, MAX_ENTRADA, MAX_LINEAS_ARCHIVO = 1500, 1200, 25
OMITIDO_MEMORIA = "[omitido: notas de memoria del asistente, con datos de otras tareas y personales]"
OMITIDO_COMENTARIOS = ("[omitido: comentarios de entrega de otros estudiantes del issue #201; tienen nombres de "
                       "terceros y son públicos en GitHub]")


CORREOS_PERMITIDOS = {"noreply@anthropic.com"}      # el de la línea Co-Authored-By de los commits
TERMINOS = []                                        # términos de --ocultar (nombres de terceros, etc.)


def variantes_usuario():
    """El nombre de usuario de Windows tal como aparece en rutas y listados (con espacio, con guion y abreviado)."""
    nombre = Path.home().name
    corto = Path(os.environ.get("TEMP", "")).parts[2:3]
    return {nombre, nombre.replace(" ", "-"), *corto} - {""}


def _correo(m):
    return m.group(0) if m.group(0).lower() in CORREOS_PERMITIDOS else "[correo oculto]"


def ocultar(texto):
    """Sobre un texto ya decodificado: quita avisos internos, rutas personales y correos."""
    texto = re.sub(r"<system-reminder>.*?</system-reminder>", "", texto, flags=re.S)
    texto = re.sub(r"[A-Za-z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/)[^\\/\"'\n]+(?:(?:\\\\|\\|/)AppData(?:\\\\|\\|/)Local"
                   r"(?:\\\\|\\|/)Temp(?:\\\\|\\|/)claude(?:\\\\|\\|/)[^\\/\"'\n]+(?:\\\\|\\|/)[0-9a-f-]{36}"
                   r"(?:\\\\|\\|/)scratchpad)?", lambda m: "<scratchpad>" if "scratchpad" in m.group(0) else "~", texto)
    texto = re.sub(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b", _correo, texto)
    for termino in sorted(variantes_usuario(), key=len, reverse=True):
        texto = re.sub(re.escape(termino), "usuario", texto, flags=re.I)
    for termino in TERMINOS:
        texto = re.sub(re.escape(termino), "[oculto]", texto, flags=re.I)
    return texto


def ocultar_todo(x):
    """ocultar() en cada texto de un objeto JSON. Sobre el JSON ya escrito rompería los escapes («\\n@mcp.tool»)."""
    if isinstance(x, str):
        return ocultar(x)
    if isinstance(x, list):
        return [ocultar_todo(v) for v in x]
    if isinstance(x, dict):
        return {k: ocultar_todo(v) for k, v in x.items()}
    return x


def es_memoria(texto):
    return bool(re.search(r"[\\/]memory[\\/]|MEMORY\.md|=== no-commits\.md ===|name: no-commits", texto))


def hora(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(PERU)


def texto_resultado(bloque):
    c = bloque.get("content")
    if isinstance(c, list):
        c = "\n".join(x.get("text", f"[{x.get('type')}]") for x in c)
    return str(c or "")


def recortar(texto, limite):
    return texto if len(texto) <= limite else texto[:limite] + f"\n[… {len(texto) - limite} caracteres más en el .json]"


def entrada_legible(nombre, entrada):
    """La entrada de una herramienta, resumida para leer: el comando, el archivo, o el JSON recortado."""
    if nombre in ("Bash", "PowerShell"):
        return f"```bash\n{recortar(entrada.get('command', ''), MAX_ENTRADA)}\n```"
    if nombre == "Write":
        lineas = entrada.get("content", "").splitlines()
        cuerpo = "\n".join(lineas[:MAX_LINEAS_ARCHIVO])
        resto = f"\n[… {len(lineas) - MAX_LINEAS_ARCHIVO} líneas más; el archivo está en el repositorio]" \
            if len(lineas) > MAX_LINEAS_ARCHIVO else ""
        return f"Archivo: `{entrada.get('file_path')}`\n\n```\n{cuerpo}{resto}\n```"
    if nombre == "Edit":
        return (f"Archivo: `{entrada.get('file_path')}`\n\nAntes:\n```\n{recortar(entrada.get('old_string', ''), 600)}\n```"
                f"\nDespués:\n```\n{recortar(entrada.get('new_string', ''), 600)}\n```")
    if nombre == "Read":
        return f"Archivo: `{entrada.get('file_path')}`"
    return f"```json\n{recortar(json.dumps(entrada, ensure_ascii=False, indent=1), MAX_ENTRADA)}\n```"


def leer_sesion(ruta):
    """Las entradas de la conversación en orden: mensajes, respuestas, herramientas y resultados."""
    entradas, omitir = [], set()
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        d = json.loads(linea)
        if d.get("type") not in ("user", "assistant") or "message" not in d:
            continue
        ts, contenido = d["timestamp"], d["message"].get("content")
        if d["type"] == "user":
            if isinstance(contenido, str):
                if d.get("isMeta") or contenido.startswith(("<local-command-caveat>", "<local-command-stdout>")):
                    continue
                if contenido.startswith("<command-name>"):
                    nombre = re.search(r"<command-name>(.*?)</command-name>", contenido)
                    args = re.search(r"<command-args>(.*?)</command-args>", contenido, re.S)
                    entradas.append({"ts": ts, "rol": "comando", "texto": f"{nombre.group(1)} {args.group(1) if args else ''}".strip()})
                    continue
                entradas.append({"ts": ts, "rol": "usuario", "texto": contenido})
                continue
            for b in contenido or []:
                if b.get("type") == "tool_result":
                    texto = texto_resultado(b)
                    if b.get("tool_use_id") in omitir or es_memoria(texto):
                        texto = OMITIDO_MEMORIA
                    elif "AUTHOR: " in texto and "Tarea 4" in texto:
                        texto = OMITIDO_COMENTARIOS
                    entradas.append({"ts": ts, "rol": "resultado", "error": bool(b.get("is_error")), "texto": texto})
                elif b.get("type") == "text" and d.get("isMeta"):
                    primera = b["text"].strip().splitlines()[0] if b["text"].strip() else ""
                    if primera.startswith("Base directory for this skill"):
                        entradas.append({"ts": ts, "rol": "nota", "texto": "Se cargó la guía de una skill: "
                                         + Path(primera.split(":", 1)[1].strip()).name})
                elif b.get("type") == "text" and not d.get("isMeta"):
                    entradas.append({"ts": ts, "rol": "usuario", "texto": b["text"]})
        else:
            for b in contenido or []:
                if b.get("type") == "text" and b["text"].strip():
                    entradas.append({"ts": ts, "rol": "claude", "texto": b["text"], "modelo": d["message"].get("model")})
                elif b.get("type") == "tool_use":
                    entrada = b.get("input", {})
                    if es_memoria(json.dumps(entrada, ensure_ascii=False)):
                        omitir.add(b.get("id"))
                        entrada = {"nota": OMITIDO_MEMORIA}
                    entradas.append({"ts": ts, "rol": "herramienta", "nombre": b.get("name"), "entrada": entrada})
    return entradas


def fases(entradas, definiciones):
    """Corta la conversación en fases según el primer mensaje del usuario que contiene cada texto."""
    inicios = []
    for carpeta, titulo, texto in definiciones:
        if not texto:
            inicios.append((0, carpeta, titulo))
            continue
        i = next((i for i, e in enumerate(entradas) if e["rol"] == "usuario" and texto.lower() in e["texto"].lower()),
                 None)
        if i is None:
            raise SystemExit(f"No encontré un mensaje del usuario con {texto!r} para la fase {carpeta}.")
        inicios.append((i, carpeta, titulo))
    inicios.sort()
    return [(carpeta, titulo, entradas[i:(inicios[k + 1][0] if k + 1 < len(inicios) else len(entradas))])
            for k, (i, carpeta, titulo) in enumerate(inicios)]


def markdown(titulo, entradas, sesion):
    modelos = sorted({e["modelo"] for e in entradas if e.get("modelo")})
    n_usuario = sum(e["rol"] == "usuario" for e in entradas)
    n_herr = sum(e["rol"] == "herramienta" for e in entradas)
    md = [f"# Conversación con Claude Code: {titulo}", "",
          f"- **Sesión:** `{sesion[:8]}` · **modelo:** {', '.join(modelos) or '—'}",
          f"- **Desde** {hora(entradas[0]['ts']):%Y-%m-%d %H:%M} **hasta** {hora(entradas[-1]['ts']):%Y-%m-%d %H:%M} "
          "(hora de Perú)",
          f"- **Mensajes del usuario:** {n_usuario} · **herramientas usadas por Claude:** {n_herr}",
          "- Exportado con `scripts/exportar_conversacion.py` desde el registro que guarda Claude Code. Incluye cada "
          "mensaje, respuesta, herramienta y resultado (los resultados largos se recortan aquí y están completos en "
          "`00_conversacion.json`). No incluye el razonamiento interno del modelo ni mensajes internos de Claude Code. "
          "Se ocultaron rutas personales, correos, las notas de memoria del asistente y nombres de terceros.", ""]
    for e in entradas:
        t = f"{hora(e['ts']):%H:%M}"
        if e["rol"] == "usuario":
            md += [f"### 🧑 Usuario · {t}", "", "> " + ocultar(e["texto"]).strip().replace("\n", "\n> "), ""]
        elif e["rol"] == "comando":
            md += [f"*{t} · el usuario ejecutó `{e['texto']}` en Claude Code*", ""]
        elif e["rol"] == "nota":
            md += [f"*{t} · {e['texto']}*", ""]
        elif e["rol"] == "claude":
            md += [f"**🤖 Claude · {t}:** {ocultar(e['texto']).strip()}", ""]
        elif e["rol"] == "herramienta":
            md += [f"<details><summary>🔧 {e['nombre']} · {t}</summary>", "",
                   ocultar(entrada_legible(e["nombre"], e["entrada"])), ""]
        elif e["rol"] == "resultado":
            md += [f"**Resultado{' (error)' if e['error'] else ''}:**", "", "```",
                   recortar(ocultar(e["texto"]).strip(), MAX_RESULTADO), "```", "", "</details>", ""]
    return "\n".join(md) + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sesion", type=Path)
    p.add_argument("--fase", action="append", required=True, help="carpeta|título|texto del primer mensaje")
    p.add_argument("--salida", type=Path, default=RAIZ / "evidencias_ia")
    p.add_argument("--ocultar", type=Path, help="archivo (fuera del repositorio) con un término por línea que se oculta")
    a = p.parse_args()
    if a.ocultar:
        TERMINOS.extend(sorted({t.strip() for t in a.ocultar.read_text(encoding="utf-8").splitlines() if len(t.strip()) > 3},
                               key=len, reverse=True))
    entradas = leer_sesion(a.sesion)
    definiciones = [tuple(f.split("|", 2)) for f in a.fase]
    for carpeta, titulo, parte in fases(entradas, definiciones):
        destino = a.salida / carpeta
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "00_conversacion.md").write_text(markdown(titulo, parte, a.sesion.stem), encoding="utf-8")
        limpio = [ocultar_todo(e) | {"hora_peru": f"{hora(e['ts']):%Y-%m-%d %H:%M:%S}"} for e in parte]
        (destino / "00_conversacion.json").write_text(json.dumps(limpio, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{carpeta}: {len(parte)} entradas → {(destino / '00_conversacion.md').relative_to(a.salida.parent).as_posix()}")
