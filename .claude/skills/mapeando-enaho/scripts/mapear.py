"""Mapa coroplético de la pobreza monetaria por departamento con la ENAHO, a partir de la base de limpiando-enaho.

    uv run .claude/skills/mapeando-enaho/scripts/mapear.py
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --resaltar Piura

Une la pobreza de cada departamento (ubigeo[:2] de la ENAHO) con su polígono por el código oficial (FIRST_IDDP del
GeoJSON del curso), nunca por el nombre. Exige las 25 unidades con dato, con Lima (15) y el Callao (07) separados, y
compara cada cifra con la referencia de la Sesión 16. Pondera con factor07 × mieperho, el método del INEI.

Salidas: mapas/pobreza_departamento_2024.png (200 dpi) con su CSV, y salidas/comparacion_mapa.csv.
"""
import argparse
import sys
import textwrap
import unicodedata
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from shapely.ops import polylabel  # noqa: E402

GEOJSON = ("datos/geo/peru_departamental_simple.geojson", "https://raw.githubusercontent.com/d2cml-ai/"
           "Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson")
REFERENCIA = ("datos/referencias/pobreza_departamento_2024.csv", "https://raw.githubusercontent.com/d2cml-ai/"
              "Data-Science-Python/main/sessions/16-skills-enaho/referencias/pobreza_departamento_2024.csv")
PCT = chr(0xA0) + "%"           # espacio sin corte antes del «%»: no se separa al partir el título
PROYECCION = "ESRI:102033"      # cónica equivalente de Albers para Sudamérica: las áreas se comparan bien
# Rampa de un tono validada con validate_palette.py --ordinal (pasos 250, 350, 500, 600 y 700 del azul)
CLASES = ["#86b6ef", "#5598e7", "#256abf", "#184f95", "#0d366b"]
FONDO = "#fcfcfb"
TINTA = {"primaria": "#0b0b0b", "secundaria": "#52514e", "tenue": "#898781"}
DPI = 200
# Departamentos demasiado pequeños para una etiqueta adentro: van al mar con una guía (desplazamiento en metros)
AL_MAR = {"07": (-230_000, 40_000), "24": (-190_000, 70_000)}
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "text.color": TINTA["primaria"]})


def sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


def pct(x):
    return f"{x:.1f}{PCT}"            # espacio sin corte: el «%» no queda solo en otra línea


def centro(geometria):
    """El punto más interior del polígono (o de su parte más grande): ahí cabe mejor la etiqueta."""
    if geometria.geom_type == "MultiPolygon":
        geometria = max(geometria.geoms, key=lambda g: g.area)
    return polylabel(geometria, tolerance=1000)


def asegurar(ruta, url):
    ruta = Path(ruta)
    if not ruta.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(url, timeout=120, follow_redirects=True)
        r.raise_for_status()
        ruta.write_bytes(r.content)
        print(f"Bajado {ruta.as_posix()} desde {url}")
    return ruta


def pobreza_departamental(salidas, anio=2024):
    hogares = salidas / f"hogares_{anio}.parquet"
    if not hogares.exists():
        raise SystemExit(f"Falta {hogares.as_posix()}: usa primero la skill limpiando-enaho "
                         "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py) y vuelve a mapear.")
    h = pd.read_parquet(hogares)
    h = h.assign(_pobres=h.peso_inei * h.pobre)
    t = h.groupby(["ccdd", "departamento"], as_index=False).agg(poblacion=("peso_inei", "sum"),
                                                               pobres=("_pobres", "sum"), n_hogares=("ccdd", "size"))
    t["pobreza_pct"] = 100 * t.pobres / t.poblacion
    nacional = 100 * h._pobres.sum() / h.peso_inei.sum()
    return t, nacional


def unir(t, geo):
    """La unión por código oficial: ubigeo[:2] (ccdd) con FIRST_IDDP, los dos como texto de 2 dígitos."""
    geo = geo.assign(ccdd=geo.FIRST_IDDP.astype(str).str.zfill(2))
    errores = []
    if len(t) != 25 or sorted(t.ccdd) != [f"{i:02d}" for i in range(1, 26)]:
        errores.append(f"la ENAHO trae {len(t)} códigos de departamento, no los 25 del INEI")
    if geo.ccdd.duplicated().any() or len(geo) != 25:
        errores.append(f"el GeoJSON trae {len(geo)} polígonos o códigos repetidos, no 25 únicos")
    mapa = geo.merge(t, on="ccdd", how="outer", validate="1:1", indicator=True)
    sin_par = mapa[mapa._merge != "both"]
    if len(sin_par):
        errores.append(f"códigos sin pareja: {sorted(sin_par.ccdd)}")
    if mapa.pobreza_pct.isna().any():
        errores.append("hay departamentos sin dato de pobreza")
    if not {"07", "15"} <= set(mapa.ccdd) or mapa.loc[mapa.ccdd.isin(["07", "15"]), "pobreza_pct"].nunique() != 2:
        errores.append("Lima (15) y el Callao (07) no quedaron como dos unidades separadas")
    if errores:
        raise SystemExit("UNIÓN FALLIDA: " + "; ".join(errores) + ". No se dibuja el mapa.")
    distintos = (mapa.NOMBDEP.map(sin_tildes) != mapa.departamento.map(sin_tildes)).sum()
    print(f"Unión por código: 25 de 25 departamentos con dato; nombres que difieren tras quitar tildes: {distintos}.")
    return gpd.GeoDataFrame(mapa.drop(columns="_merge"), geometry="geometry", crs=geo.crs)


def comparar(mapa, salidas):
    ref = pd.read_csv(asegurar(*REFERENCIA), dtype={"ccdd": str})
    c = mapa[["ccdd", "departamento", "pobreza_pct"]].merge(ref[["ccdd", "pobreza_pct"]], on="ccdd",
                                                            suffixes=("_calculada", "_referencia"))
    c["diferencia_pp"] = (c.pobreza_pct_calculada - c.pobreza_pct_referencia).round(2)
    c["pobreza_pct_calculada"] = c.pobreza_pct_calculada.round(2)
    c.sort_values("ccdd").to_csv(salidas / "comparacion_mapa.csv", index=False, encoding="utf-8")
    maximo = c.diferencia_pp.abs().max()
    print(f"Comparación con la referencia de la Sesión 16: {len(c)} departamentos, diferencia máxima {maximo:.2f} "
          f"puntos; {int((c.diferencia_pp.abs() <= 0.1).sum())} de {len(c)} a 0.1 puntos o menos. "
          f"Detalle en {(salidas / 'comparacion_mapa.csv').as_posix()}")
    return maximo


def dibujar(mapa, nacional, maximo_dif, archivo, resaltar=None):
    tope = 50 if mapa.pobreza_pct.max() < 50 else float(np.ceil(mapa.pobreza_pct.max() / 10) * 10)
    cortes = np.linspace(0, tope, len(CLASES) + 1)
    mapa = mapa.to_crs(PROYECCION)
    mapa["clase"] = np.clip(np.digitize(mapa.pobreza_pct, cortes[1:-1]), 0, len(CLASES) - 1)
    alto_dep, bajo_dep = mapa.loc[mapa.pobreza_pct.idxmax()], mapa.loc[mapa.pobreza_pct.idxmin()]

    fig = plt.figure(figsize=(7.6, 9.4), dpi=DPI, facecolor=FONDO)
    ax = fig.add_axes([0.0, 0.065, 1.0, 0.8], facecolor=FONDO)
    mapa.plot(ax=ax, color=[CLASES[c] for c in mapa.clase], edgecolor=FONDO, linewidth=0.7)
    if resaltar:
        elegido = mapa[mapa.departamento.map(sin_tildes) == sin_tildes(resaltar)]
        if elegido.empty:
            raise SystemExit(f"No existe el departamento {resaltar!r}.")
        elegido.boundary.plot(ax=ax, color=TINTA["primaria"], linewidth=1.6)
    for fila in mapa.itertuples():
        punto = centro(fila.geometry)
        tinta = "#ffffff" if fila.clase >= 2 else TINTA["primaria"]
        nombre = fila.departamento
        destacado = resaltar and sin_tildes(nombre) == sin_tildes(resaltar)
        if fila.ccdd in AL_MAR:
            dx, dy = AL_MAR[fila.ccdd]
            ax.annotate(f"{nombre}\n{fila.pobreza_pct:.1f}", xy=(punto.x, punto.y), xytext=(punto.x + dx, punto.y + dy),
                        ha="right", va="center", size=7, color=TINTA["primaria"], linespacing=1.0,
                        weight="bold" if destacado else "normal",
                        arrowprops={"arrowstyle": "-", "color": TINTA["secundaria"], "linewidth": 0.6})
            continue
        ax.text(punto.x, punto.y, f"{nombre}\n{fila.pobreza_pct:.1f}", ha="center", va="center", size=6.6,
                color=tinta, linespacing=1.0, weight="bold" if destacado else "normal")
    ax.set_axis_off()
    ax.set_aspect("equal")

    cuantos = [int((mapa.clase == i).sum()) for i in range(len(CLASES))]
    etiquetas = [f"{cortes[i]:.0f} a {cortes[i + 1]:.0f} %  ({k} departamento{'s' if k != 1 else ''})"
                 for i, k in enumerate(cuantos)]
    ax.legend(handles=[Patch(facecolor=c, label=e) for c, e in zip(CLASES, etiquetas)], loc="lower left",
              title="Pobreza monetaria, % de la población", title_fontsize=8.5, fontsize=8, frameon=False,
              alignment="left", handlelength=1.2, handleheight=1.1, labelcolor=TINTA["secundaria"])

    titulo = (f"La pobreza va de {pct(bajo_dep.pobreza_pct)} en {bajo_dep.departamento} a "
              f"{pct(alto_dep.pobreza_pct)} en {alto_dep.departamento}")
    if resaltar:
        f = mapa[mapa.departamento.map(sin_tildes) == sin_tildes(resaltar)].iloc[0]
        titulo += f"; {f.departamento} tiene {pct(f.pobreza_pct)}"
    lineas = textwrap.wrap(titulo, 70)
    fig.text(0.035, 0.975, "\n".join(lineas), size=12.5, weight="bold", va="top", linespacing=1.15)
    fig.text(0.035, 0.975 - 0.032 * len(lineas) - 0.012, f"Pobreza monetaria por departamento, % de la población, "
             f"Perú 2024 (total nacional: {pct(nacional)})", size=9.5, va="top", color=TINTA["secundaria"])
    nota = ("Fuente: INEI, ENAHO 2024, módulos 34 y 02; límites departamentales del repositorio del curso. "
            "Elaboración propia. Ponderado con factor07 × mieperho (método del INEI). Unión por código: "
            f"ubigeo[:2] = FIRST_IDDP. Diferencia máxima con la referencia de la Sesión 16: {maximo_dif:.2f} puntos.")
    fig.text(0.035, 0.012, "\n".join(textwrap.wrap(nota, 125)), size=7.2, va="bottom", color=TINTA["tenue"])
    archivo.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(archivo, dpi=DPI, facecolor=FONDO)
    plt.close(fig)
    (mapa.drop(columns="geometry")[["ccdd", "departamento", "pobreza_pct", "clase", "poblacion", "pobres", "n_hogares"]]
     .assign(clase=lambda d: [etiquetas[c].split("  ")[0] for c in d.clase], pobreza_pct=lambda d: d.pobreza_pct.round(2),
             poblacion=lambda d: d.poblacion.round(0), pobres=lambda d: d.pobres.round(0))
     .sort_values("ccdd").to_csv(archivo.with_suffix(".csv"), index=False, encoding="utf-8"))
    return archivo


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--resaltar", help="departamento que se marca con un borde, p. ej. Piura")
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--mapas", type=Path, default=Path("mapas"))
    a = p.parse_args()
    tabla, nacional = pobreza_departamental(a.salidas)
    mapa = unir(tabla, gpd.read_file(asegurar(*GEOJSON)))
    maximo = comparar(mapa, a.salidas)
    nombre = "pobreza_departamento_2024" + (f"_{sin_tildes(a.resaltar).replace(' ', '_')}" if a.resaltar else "")
    archivo = dibujar(mapa, nacional, maximo, a.mapas / f"{nombre}.png", a.resaltar)
    print(f"Mapa: {archivo.as_posix()} y {archivo.with_suffix('.csv').as_posix()}")
