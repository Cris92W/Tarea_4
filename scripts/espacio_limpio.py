"""Arma una copia limpia del proyecto para correr a Claude Code desde cero, sin ninguna salida previa.

    uv run scripts/espacio_limpio.py <carpeta_nueva>
    uv run scripts/espacio_limpio.py <carpeta_nueva> --sin-referencias      # para la evaluación

Copia el código, las Skills, el servidor MCP y los microdatos originales; no copia salidas/, figuras/, mapas/,
informes/, evaluacion/, evidencias_ia/ ni el README. Así la skill de limpieza tiene que correr antes que las de
gráficos y mapas, y en la evaluación el agente no puede leer cifras ya calculadas. Con --sin-referencias tampoco
copia la referencia de la Sesión 16. La carpeta de destino debe ser nueva: nunca se borra nada.
"""
import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
COPIAR = ["pyproject.toml", "uv.lock", ".python-version", ".mcp.json", ".gitignore", "mcp/server.py", ".claude/skills",
          "datos/enaho", "datos/geo", "datos/bcrp/catalogo_bcrp.csv"]
REFERENCIAS = "datos/referencias"
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "settings.local.json")


def espacio_limpio(destino, referencias=True):
    destino = Path(destino)
    if destino.exists() and any(destino.iterdir()):
        raise SystemExit(f"{destino} ya existe y no está vacía: elijan otra carpeta (este script no borra nada).")
    for relativa in COPIAR + ([REFERENCIAS] if referencias else []):
        origen = RAIZ / relativa
        if not origen.exists():
            continue
        final = destino / relativa
        final.parent.mkdir(parents=True, exist_ok=True)
        if origen.is_dir():
            shutil.copytree(origen, final, ignore=IGNORAR)
        else:
            shutil.copy2(origen, final)
    print(f"Copia limpia en {destino} ({sum(1 for p in destino.rglob('*') if p.is_file())} archivos).")
    return destino


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("destino")
    p.add_argument("--sin-referencias", action="store_true")
    a = p.parse_args()
    espacio_limpio(a.destino, referencias=not a.sin_referencias)
