"""Baja los módulos 34 (sumaria) y 02 (miembros del hogar) de la ENAHO del portal de microdatos del INEI.

    uv run .claude/skills/limpiando-enaho/scripts/descargar.py            # ENAHO 2024 en datos/enaho/

966 es el código de la ENAHO 2024 en el portal del INEI. Si un zip ya está y se puede abrir, no se vuelve a bajar.
Los zip quedan en datos/, que no se sube a GitHub.
"""
import argparse
import sys
import zipfile
from pathlib import Path

import httpx

URL = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"
CODIGOS = {2024: 966}
MODULOS = {"34": "sumaria, una fila por hogar", "02": "miembros del hogar, una fila por persona"}


def descargar(anio=2024, carpeta=Path("datos/enaho")):
    if anio not in CODIGOS:
        raise SystemExit(f"No conozco el código del INEI para la ENAHO {anio}; solo {sorted(CODIGOS)}.")
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for modulo, que_es in MODULOS.items():
        url = URL.format(codigo=CODIGOS[anio], modulo=modulo)
        destino = carpeta / Path(url).name
        if destino.exists() and zipfile.is_zipfile(destino):
            print(f"Ya está {destino} ({que_es}).")
        else:
            parcial = destino.with_suffix(".part")
            with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
                r.raise_for_status()
                with parcial.open("wb") as f:
                    for trozo in r.iter_bytes(1 << 20):
                        f.write(trozo)
            if not zipfile.is_zipfile(parcial):
                parcial.unlink()
                raise SystemExit(f"El INEI no devolvió un zip válido en {url}. Bájenlo desde el navegador a {carpeta}/.")
            parcial.replace(destino)
            print(f"Bajado {destino} ({destino.stat().st_size / 1e6:.1f} MB, {que_es}) desde {url}")
        rutas.append(destino)
    return rutas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--carpeta", type=Path, default=Path("datos/enaho"))
    a = p.parse_args()
    descargar(a.anio, a.carpeta)
