"""Gráficos de pobreza monetaria con la ENAHO, a partir de la base que deja la skill limpiando-enaho.

    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo area
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo departamento --resaltar Piura
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo todos

Tipos: area (urbana y rural), sexo (de la persona y de quien encabeza el hogar), edad (5 grupos), departamento (25)
y dominio (8). Cada barra es la pobreza monetaria total; el tramo oscuro es la pobreza extrema. Las cifras se
ponderan: territorios y tipos de hogar con factor07 × mieperho (el método del INEI); rasgos de la persona con
facpob07. Cada PNG (200 dpi, en figuras/) sale con un CSV gemelo con las cifras graficadas.
"""
import argparse
import sys
import textwrap
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle  # noqa: E402

# Paleta validada con validate_palette.py --ordinal (rampa de un solo tono, contraste del tono claro >= 2:1)
FONDO = "#fcfcfb"
TINTA = {"primaria": "#0b0b0b", "secundaria": "#52514e", "tenue": "#898781", "rejilla": "#e1e0d9", "base": "#c3c2b7"}
AZUL = {"no_extrema": "#6da7ec", "extrema": "#184f95"}
GRIS = {"no_extrema": "#b0aea6", "extrema": "#77756f"}
DPI, ANCHO = 200, 8.0                   # pulgadas
RADIO_PX, HUECO_PX = 4 * DPI / 96, 2 * DPI / 96
FUENTE = "Fuente: INEI, Encuesta Nacional de Hogares (ENAHO) 2024, módulos 34 y 02. Elaboración propia."
POR_HOGARES = "Ponderado con factor07 × mieperho (método del INEI)."
PCT = chr(0xA0) + "%"           # espacio sin corte antes del «%»: no se separa al partir el título
POR_PERSONAS = "Ponderado con facpob07 (residentes habituales)."
TIPOS = ["area", "sexo", "edad", "departamento", "dominio"]

plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": TINTA["base"],
                     "text.color": TINTA["primaria"], "xtick.color": TINTA["tenue"], "ytick.color": TINTA["primaria"]})


def tasa(df, columna, peso):
    return 100 * (df[columna] * df[peso]).sum() / df[peso].sum()


def cargar(salidas, anio=2024):
    personas, hogares = salidas / f"personas_{anio}.parquet", salidas / f"hogares_{anio}.parquet"
    if not personas.exists() or not hogares.exists():
        raise SystemExit(f"Falta {personas.as_posix()}: usa primero la skill limpiando-enaho "
                         "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py) y vuelve a graficar.")
    return pd.read_parquet(personas), pd.read_parquet(hogares)


def tabla(df, por, peso, orden=None):
    filas = [{"categoria": k, "pobreza_pct": tasa(g, "pobre", peso), "pobreza_extrema_pct": tasa(g, "pobre_extremo", peso),
              "poblacion": g[peso].sum(), "n_muestra": len(g)}
             for k, g in df.groupby(por, observed=True)]
    t = pd.DataFrame(filas)
    if orden is not None:
        return t.set_index("categoria").loc[orden].reset_index()
    return t.sort_values("pobreza_pct", ascending=False, ignore_index=True)


def sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


# ------------------------------------------------------------------------------------------------- dibujo

def lienzo(n, izquierda, lineas_titulo):
    banda, pie = 0.36, 0.95
    cabeza = 0.3 + 0.27 * lineas_titulo + 0.95          # título + subtítulo + leyenda + aire
    alto_ejes = n * banda + 0.3                           # + espacio para la etiqueta de la línea nacional
    alto = cabeza + alto_ejes + pie
    fig = plt.figure(figsize=(ANCHO, alto), dpi=DPI, facecolor=FONDO)
    ax = fig.add_axes([izquierda / ANCHO, pie / alto, (ANCHO - izquierda - 0.55) / ANCHO, alto_ejes / alto],
                      facecolor=FONDO)
    return fig, ax, alto


def barra(ax, y, x0, x1, alto, color, redondear):
    """Una barra horizontal: recta en la base y con el extremo de datos redondeado (4 px)."""
    if x1 <= x0:
        return
    ppx = ax.bbox.width / np.diff(ax.get_xlim())[0]
    ppy = ax.bbox.height / np.diff(ax.get_ylim())[0]
    if redondear:
        r = min(RADIO_PX / ppx, (x1 - x0) / 2)
        ax.add_patch(FancyBboxPatch((x0, y - alto / 2), x1 - x0, alto, boxstyle=f"round,pad=0,rounding_size={r}",
                                    mutation_aspect=ppx / ppy, facecolor=color, linewidth=0, zorder=3))
        ax.add_patch(Rectangle((x0, y - alto / 2), max(x1 - x0 - r, 0), alto, facecolor=color, linewidth=0, zorder=3))
    else:
        ax.add_patch(Rectangle((x0, y - alto / 2), x1 - x0, alto, facecolor=color, linewidth=0, zorder=3))


def grafico(t, titulo, subtitulo, nota, archivo, nacional=None, resaltar=None, etiquetas_dentro=True, izquierda=1.3,
            secciones=None, etiqueta_nacional="Perú"):
    """Barras horizontales apiladas: pobreza extrema (oscuro) + no extrema (claro) = pobreza total."""
    n = len(t)
    titulo_lineas = textwrap.wrap(titulo, 78)
    fig, ax, alto = lienzo(n, izquierda, len(titulo_lineas))
    tope = max(10, np.ceil(t.pobreza_pct.max() / 10) * 10 + 5)
    ax.set_xlim(0, tope)
    ax.set_ylim(-0.6, n - 0.4 + 0.85)                    # arriba queda la etiqueta de la línea nacional
    ys = np.arange(n)[::-1]                      # la primera fila arriba
    alto_barra = 0.56
    ppx = ax.bbox.width / tope
    renderer = fig.canvas.get_renderer()
    for y, fila in zip(ys, t.itertuples()):
        destacado = resaltar is None or sin_tildes(fila.categoria) == sin_tildes(resaltar)
        colores = AZUL if destacado else GRIS
        extrema, total = fila.pobreza_extrema_pct, fila.pobreza_pct
        inicio = 0
        if extrema * ppx >= 1.5:                 # un tramo de menos de 1.5 px no se ve: queda en el CSV
            barra(ax, y, 0, extrema, alto_barra, colores["extrema"], redondear=False)
            inicio = extrema + HUECO_PX / ppx
        barra(ax, y, inicio, total, alto_barra, colores["no_extrema"], redondear=True)
        peso = "bold" if resaltar is not None and destacado else "normal"
        ax.text(total + 6 / ppx, y, f"{total:.1f}{PCT}", va="center", ha="left", size=9, weight=peso,
                color=TINTA["primaria"], zorder=6,       # el fondo tapa la línea nacional donde se cruzan
                bbox={"facecolor": FONDO, "edgecolor": "none", "pad": 0.8})
        if etiquetas_dentro and extrema > 0:
            t_in = ax.text(extrema / 2, y, f"{extrema:.1f}", va="center", ha="center", size=7.5, color="#ffffff",
                           zorder=5)
            if t_in.get_window_extent(renderer).width + 8 > extrema * ppx:    # no cabe con aire: se quita
                t_in.remove()
    ax.set_yticks(ys, [str(c) for c in t.categoria])
    for etiqueta, fila in zip(ax.get_yticklabels(), t.itertuples()):
        if resaltar is not None and sin_tildes(fila.categoria) == sin_tildes(resaltar):
            etiqueta.set_fontweight("bold")
    ax.tick_params(axis="y", length=0, pad=6, labelsize=9)
    ax.tick_params(axis="x", length=0, labelsize=8)
    marcas = np.arange(0, tope + 0.1, 10)
    ax.set_xticks(marcas, [f"{m:.0f} %" for m in marcas])
    ax.grid(axis="x", color=TINTA["rejilla"], linewidth=0.8, zorder=0)
    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)
    ax.axvline(0, color=TINTA["base"], linewidth=1, zorder=2)
    if nacional is not None:
        ax.plot([nacional, nacional], [-0.6, n - 0.4 + 0.25], color=TINTA["secundaria"], linewidth=0.9, zorder=2)
        ax.text(nacional, n - 0.4 + 0.3, f"{etiqueta_nacional} {nacional:.1f}{PCT}", ha="center", va="bottom", size=8,
                color=TINTA["secundaria"])
    if secciones:
        for y_corte in secciones:
            ax.axhline(y_corte, color=TINTA["rejilla"], linewidth=0.8, zorder=1)
    margen = 0.25 / ANCHO
    fig.text(margen, 1 - 0.22 / alto, "\n".join(titulo_lineas), size=12.5, weight="bold", va="top",
             color=TINTA["primaria"], linespacing=1.15)
    y_sub = 1 - (0.36 + 0.27 * len(titulo_lineas)) / alto
    if resaltar is not None:
        subtitulo += f". {resaltar} resaltado"
    fig.text(margen, y_sub, subtitulo, size=9.5, va="top", color=TINTA["secundaria"])
    colores_leyenda = GRIS if resaltar is not None else AZUL
    leyenda = [Patch(facecolor=colores_leyenda["extrema"], label="Pobreza extrema"),
               Patch(facecolor=colores_leyenda["no_extrema"],
                     label="Pobreza no extrema (la barra completa es la pobreza total)")]
    fig.legend(handles=leyenda, loc="upper left", bbox_to_anchor=(margen - 0.004, y_sub - 0.2 / alto), ncol=2,
               frameon=False, fontsize=8.5, handlelength=1.1, handleheight=1.1, columnspacing=1.6,
               labelcolor=TINTA["secundaria"])
    fig.text(margen, 0.12 / alto, "\n".join(textwrap.wrap(f"{FUENTE} {nota}", 120)), size=7.5, va="bottom",
             color=TINTA["tenue"])
    archivo.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(archivo, dpi=DPI, facecolor=FONDO)
    plt.close(fig)
    t.round(2).to_csv(archivo.with_suffix(".csv"), index=False, encoding="utf-8")
    return archivo


# ------------------------------------------------------------------------------------------------- tipos

def g_area(personas, hogares, carpeta, **_):
    t = tabla(hogares, "area", "peso_inei", orden=["Urbana", "Rural"])
    u, r = t.pobreza_pct
    nac = tasa(hogares, "pobre", "peso_inei")
    titulo = f"La pobreza rural ({r:.1f}{PCT}) supera en {r - u:.1f} puntos a la urbana ({u:.1f}{PCT})"
    return grafico(t, titulo, "Pobreza monetaria según área de residencia, % de la población, Perú 2024",
                   f"{POR_HOGARES} Urbana: centros poblados de 2 000 habitantes o más (estrato 1 a 5).",
                   carpeta / "pobreza_area.png", nacional=nac, izquierda=1.0)


def g_sexo(personas, hogares, carpeta, **_):
    p = tabla(personas, "sexo", "facpob07", orden=["Mujer", "Hombre"])
    p["categoria"] = ["Mujeres", "Hombres"]
    h = tabla(hogares, "sexo_jefe", "peso_inei", orden=["Mujer", "Hombre"])
    h["categoria"] = ["Hogar con jefa", "Hogar con jefe"]
    t = pd.concat([p, h], ignore_index=True)
    m, hom = p.pobreza_pct
    jm, jh = h.pobreza_pct
    if abs(m - hom) < 1:
        titulo = (f"Por sexo casi no hay brecha ({m:.1f}{PCT} en mujeres y {hom:.1f}{PCT} en hombres); los hogares con "
                  f"jefa son {'menos' if jm < jh else 'más'} pobres ({jm:.1f}{PCT} frente a {jh:.1f}{PCT})")
    else:
        titulo = f"La pobreza es de {m:.1f}{PCT} en mujeres y {hom:.1f}{PCT} en hombres"
    return grafico(t, titulo, "Pobreza monetaria según el sexo de la persona y de quien encabeza el hogar, %, Perú 2024",
                   f"Personas: {POR_PERSONAS} Hogares: {POR_HOGARES}", carpeta / "pobreza_sexo.png",
                   nacional=tasa(hogares, "pobre", "peso_inei"), izquierda=1.35, secciones=[1.5])


def g_edad(personas, hogares, carpeta, **_):
    grupos = ["0 a 14", "15 a 29", "30 a 44", "45 a 64", "65 y más"]
    t = tabla(personas, "grupo_edad", "facpob07", orden=grupos)
    t["categoria"] = [f"{g} años" for g in grupos]
    alto, bajo = t.loc[t.pobreza_pct.idxmax()], t.loc[t.pobreza_pct.idxmin()]
    titulo = (f"La pobreza más alta está en el grupo de {alto.categoria} ({alto.pobreza_pct:.1f}{PCT}); la más baja, "
              f"en el de {bajo.categoria} ({bajo.pobreza_pct:.1f}{PCT})")
    return grafico(t, titulo, "Pobreza monetaria por grupo de edad, % de las personas, Perú 2024",
                   f"{POR_PERSONAS} Con esa misma base, el total nacional es {tasa(personas, 'pobre', 'facpob07'):.1f}{PCT} "
                   f"(27.6 % con el método del INEI).", carpeta / "pobreza_edad.png",
                   nacional=tasa(personas, "pobre", "facpob07"), izquierda=1.1, etiqueta_nacional="Perú, residentes")


def g_departamento(personas, hogares, carpeta, resaltar=None, **_):
    t = tabla(hogares, "departamento", "peso_inei")
    alto, bajo = t.iloc[0], t.iloc[-1]
    titulo = (f"{alto.categoria} tiene la pobreza más alta ({alto.pobreza_pct:.1f}{PCT}) y {bajo.categoria} la más baja "
              f"({bajo.pobreza_pct:.1f}{PCT})")
    if resaltar:
        fila = t[t.categoria.map(sin_tildes) == sin_tildes(resaltar)]
        if fila.empty:
            raise SystemExit(f"No existe el departamento {resaltar!r}. Hay: {', '.join(t.categoria)}.")
        f = fila.iloc[0]
        titulo = (f"{f.categoria}: {f.pobreza_pct:.1f}{PCT} de pobreza, puesto {fila.index[0] + 1} de 25 departamentos "
                  f"(máximo: {alto.categoria}, {alto.pobreza_pct:.1f}{PCT})")
    nombre = f"pobreza_departamento{'_' + sin_tildes(resaltar).replace(' ', '_') if resaltar else ''}.png"
    return grafico(t, titulo, "Pobreza monetaria por departamento, % de la población, Perú 2024",
                   f"{POR_HOGARES} Lima incluye Lima Metropolitana y Lima provincias; el Callao va aparte.",
                   carpeta / nombre, nacional=tasa(hogares, "pobre", "peso_inei"), resaltar=resaltar,
                   etiquetas_dentro=False, izquierda=1.35)


def g_dominio(personas, hogares, carpeta, **_):
    t = tabla(hogares, "dominio_nombre", "peso_inei")
    alto, bajo = t.iloc[0], t.iloc[-1]
    titulo = (f"La {alto.categoria.lower()} es el dominio más pobre ({alto.pobreza_pct:.1f}{PCT}) y la "
              f"{bajo.categoria.lower()} el menos pobre ({bajo.pobreza_pct:.1f}{PCT})")
    return grafico(t, titulo, "Pobreza monetaria por dominio geográfico, % de la población, Perú 2024",
                   f"{POR_HOGARES} Lima Metropolitana incluye la provincia de Lima y el Callao.",
                   carpeta / "pobreza_dominio.png", nacional=tasa(hogares, "pobre", "peso_inei"), izquierda=1.45)


GRAFICOS = {"area": g_area, "sexo": g_sexo, "edad": g_edad, "departamento": g_departamento, "dominio": g_dominio}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--tipo", required=True, choices=TIPOS + ["todos"])
    p.add_argument("--resaltar", help="departamento que se destaca en el gráfico por departamento, p. ej. Piura")
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--figuras", type=Path, default=Path("figuras"))
    a = p.parse_args()
    personas, hogares = cargar(a.salidas)
    for tipo in TIPOS if a.tipo == "todos" else [a.tipo]:
        archivo = GRAFICOS[tipo](personas, hogares, a.figuras, resaltar=a.resaltar)
        print(f"{tipo}: {archivo.as_posix()} y {archivo.with_suffix('.csv').as_posix()}")
