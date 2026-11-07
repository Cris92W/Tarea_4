"""Cruza un indicador departamental del BCRP con la pobreza de la ENAHO, por el código del INEI de cada departamento.

    uv run .claude/skills/cruzando-bcrp-enaho/scripts/cruzar.py \
        --panel salidas/bcrp/panel_credito_directo_..._2024_2020.csv \
        --ipc salidas/bcrp/serie_PN38705PM_2020-12_2024-12.csv

Entra:
  --panel        la tabla que guarda el MCP bcrp con panel_departamental(..., anio_base=..., guardar=True)
  --ipc          (opcional) un índice de precios guardado con serie(..., guardar=True), para pasar a términos reales
  --indicadores  la tabla de limpiando-enaho (salidas/indicadores.csv): pobreza y población por departamento
Calcula por departamento el indicador por habitante (con la población que estima la ENAHO) y su variación nominal y
real entre los dos años. Mide la asociación con la pobreza con la correlación de rangos de Spearman y una prueba de
permutación, con y sin Lima y Callao, y compara los terciles de pobreza. Ninguna cifra se escribe a mano: todo sale
de los dos archivos del MCP y del de la ENAHO, y cada salida cita su fuente.

Salidas: salidas/cruce_<indicador>.csv y .json, y dos figuras en figuras/ (la variación real por departamento y la
dispersión del indicador por habitante frente a la pobreza), cada una con su CSV gemelo.
"""
import argparse
import json
import re
import sys
import textwrap
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

# Paletas validadas con validate_palette.py: terciles (rampa ordinal de un tono) y dispersión (azul + naranja)
TERCILES = {"Menor pobreza": "#86b6ef", "Pobreza media": "#256abf", "Mayor pobreza": "#0d366b"}
PUNTO, RESALTE = "#2a78d6", "#eb6834"
FONDO = "#fcfcfb"
TINTA = {"primaria": "#0b0b0b", "secundaria": "#52514e", "tenue": "#898781", "rejilla": "#e1e0d9", "base": "#c3c2b7"}
DPI, PERMUTACIONES, SEMILLA = 200, 20_000, 2024
PCT = chr(0xA0) + "%"           # espacio sin corte antes del «%»: no se separa al partir el título
ESCALAS = {"millones s/": 1e6, "millones de soles": 1e6, "miles de personas": 1e3}
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "text.color": TINTA["primaria"],
                     "xtick.color": TINTA["tenue"], "ytick.color": TINTA["tenue"]})


def sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


def spearman(x, y, semilla=SEMILLA):
    """Correlación de rangos de Spearman y su valor p de dos colas por permutación (no supone normalidad)."""
    rx, ry = pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(semilla)
    extremas = sum(abs(np.corrcoef(rx, rng.permutation(ry))[0, 1]) >= abs(rho) - 1e-12 for _ in range(PERMUTACIONES))
    return {"rho": round(rho, 3), "p_valor": round((extremas + 1) / (PERMUTACIONES + 1), 4), "n": len(rx)}


def leer(panel, ipc, indicadores):
    p = pd.read_csv(panel, dtype={"ccdd": str})
    for columna in ["valor", "valor_base", "anio", "anio_base", "unidad", "indicador", "fuente"]:
        if columna not in p.columns or p[columna].isna().all():
            raise SystemExit(f"{panel} no trae «{columna}». Vuelve a pedirlo al MCP con "
                             "panel_departamental(..., anio_base=<año>, guardar=True).")
    e = pd.read_csv(indicadores, dtype={"codigo": str})
    e = e[e.nivel == "departamento"].rename(columns={"codigo": "ccdd", "categoria": "departamento_enaho"})
    d = e[["ccdd", "departamento_enaho", "pobreza_pct", "poblacion", "metodo"]].merge(
        p, on="ccdd", how="inner", validate="1:1")
    if len(d) != 25 or len(e) != 25:
        raise SystemExit(f"La unión por código dejó {len(d)} departamentos (la ENAHO trae {len(e)} y el BCRP "
                         f"{len(p)}). Revisa que el panel tenga los 25; no se une por nombre.")
    if d[["valor", "valor_base", "pobreza_pct", "poblacion"]].isna().any().any():
        faltan = d.loc[d[["valor", "valor_base"]].isna().any(axis=1), "departamento"].tolist()
        raise SystemExit(f"Faltan datos del BCRP para {faltan}: no se calculan cifras con huecos.")
    inflacion = None
    if ipc:
        s = pd.read_csv(ipc).dropna(subset=["valor"])
        inflacion = {"codigo": s.codigo.iloc[0], "nombre": s.nombre.iloc[0], "desde": s.periodo.iloc[0],
                     "hasta": s.periodo.iloc[-1], "indice_desde": s.valor.iloc[0], "indice_hasta": s.valor.iloc[-1],
                     "inflacion_pct": round((s.valor.iloc[-1] / s.valor.iloc[0] - 1) * 100, 3), "fuente": s.fuente.iloc[0]}
    return d, inflacion


def cruzar(d, inflacion):
    unidad = str(d.unidad.iloc[0])
    escala = ESCALAS.get(sin_tildes(unidad).strip(), 1)
    anio, base = int(d.anio.iloc[0]), int(d.anio_base.iloc[0])
    d = d.assign(por_habitante=d.valor * escala / d.poblacion,
                 variacion_nominal_pct=(d.valor / d.valor_base - 1) * 100)
    if inflacion:
        d["variacion_real_pct"] = ((d.valor / d.valor_base) / (1 + inflacion["inflacion_pct"] / 100) - 1) * 100
    d["tercil_pobreza"] = pd.qcut(d.pobreza_pct.rank(method="first"), 3, labels=list(TERCILES)).astype(str)
    sin_lima_callao = d[~d.ccdd.isin(["15", "07"])]
    nacional_pc = d.valor.sum() * escala / d.poblacion.sum()
    resumen = {
        "pregunta": "asociación entre la pobreza monetaria y el indicador del BCRP por habitante, 25 departamentos",
        "indicador": d.indicador.iloc[0], "unidad": unidad, "anio": anio, "anio_base": base,
        "fuente_bcrp": d.fuente.iloc[0], "fuente_enaho": f"INEI, ENAHO 2024 ({d.metodo.iloc[0]})",
        "n_departamentos": len(d),
        "nacional": {"total": round(d.valor.sum(), 2), "total_base": round(d.valor_base.sum(), 2),
                     "por_habitante": round(nacional_pc, 2),
                     "variacion_nominal_pct": round((d.valor.sum() / d.valor_base.sum() - 1) * 100, 2)},
        "concentracion_lima_pct": round(100 * d.loc[d.ccdd == "15", "valor"].sum() / d.valor.sum(), 2),
        "por_habitante_max": d.loc[d.por_habitante.idxmax(), ["departamento", "por_habitante"]].to_dict(),
        "por_habitante_min": d.loc[d.por_habitante.idxmin(), ["departamento", "por_habitante"]].to_dict(),
        "brecha_max_min": round(d.por_habitante.max() / d.por_habitante.min(), 1),
        "spearman_pobreza_vs_por_habitante": spearman(d.pobreza_pct, d.por_habitante),
        "spearman_sin_lima_callao": spearman(sin_lima_callao.pobreza_pct, sin_lima_callao.por_habitante),
    }
    if inflacion:
        resumen["inflacion"] = inflacion
        resumen["nacional"]["variacion_real_pct"] = round(
            ((d.valor.sum() / d.valor_base.sum()) / (1 + inflacion["inflacion_pct"] / 100) - 1) * 100, 2)
        resumen["departamentos_con_caida_real"] = int((d.variacion_real_pct < 0).sum())
        resumen["spearman_pobreza_vs_variacion_real"] = spearman(d.pobreza_pct, d.variacion_real_pct)
    columnas = {"n": ("ccdd", "size"), "pobreza_mediana": ("pobreza_pct", "median"),
                "por_habitante_mediana": ("por_habitante", "median"),
                "variacion_nominal_mediana": ("variacion_nominal_pct", "median")}
    if inflacion:
        columnas["variacion_real_mediana"] = ("variacion_real_pct", "median")
    terciles = d.groupby("tercil_pobreza").agg(**columnas).reindex(list(TERCILES)).round(2)
    terciles["departamentos"] = [", ".join(d[d.tercil_pobreza == t].sort_values("pobreza_pct").departamento)
                                 for t in terciles.index]
    resumen["terciles_de_pobreza"] = terciles.reset_index().to_dict("records")
    return d, resumen


# --------------------------------------------------------------------------------------------- figuras

def encabezado(fig, titulo, subtitulo, nota, alto):
    lineas = textwrap.wrap(titulo, 78)
    fig.text(0.25 / 8, 1 - 0.22 / alto, "\n".join(lineas), size=12.5, weight="bold", va="top", linespacing=1.15)
    sub = textwrap.wrap(subtitulo, 105)
    fig.text(0.25 / 8, 1 - (0.36 + 0.27 * len(lineas)) / alto, "\n".join(sub), size=9.5, va="top",
             color=TINTA["secundaria"])
    fig.text(0.25 / 8, 0.12 / alto, "\n".join(textwrap.wrap(nota, 120)), size=7.5, va="bottom", color=TINTA["tenue"])
    return len(lineas) + len(sub) - 1


POSICIONES = [(5, 3), (5, -11), (-5, 3), (-5, -11), (0, 9), (0, -16), (9, 12), (9, -19), (-9, 12), (-9, -19)]


def _anotar(ax, x, y, nombre, destacado, dx, dy):
    return ax.annotate(nombre, (x, y), xytext=(dx, dy), textcoords="offset points",
                       ha="left" if dx > 0 else "right" if dx < 0 else "center", size=7.2, zorder=5,
                       color=TINTA["primaria"] if destacado else TINTA["secundaria"],
                       weight="bold" if destacado else "normal")


def etiquetar(fig, ax, xs, ys, nombres, destacados):
    """Pone cada nombre junto a su punto en la primera posición que no choca con otra etiqueta ni con un punto.

    Si ninguna de las posiciones está libre, usa la primera: nunca se pierde un nombre.
    """
    renderer = fig.canvas.get_renderer()
    radio = 10                                       # píxeles alrededor de cada punto que no se tapan
    ocupadas = [Bbox.from_bounds(px - radio, py - radio, 2 * radio, 2 * radio)
                for px, py in ax.transData.transform(np.column_stack([xs, ys]))]
    for x, y, nombre, es in sorted(zip(xs, ys, nombres, destacados), key=lambda t: (not t[3], -t[1])):
        for dx, dy in POSICIONES:
            t = _anotar(ax, x, y, nombre, es, dx, dy)
            caja = t.get_window_extent(renderer).expanded(1.04, 1.12)
            if not any(caja.overlaps(o) for o in ocupadas):
                break
            t.remove()
        else:
            t = _anotar(ax, x, y, nombre, es, *POSICIONES[0])
            caja = t.get_window_extent(renderer)
        ocupadas.append(caja)


def ejes_limpios(ax):
    for lado in ("top", "right", "left", "bottom"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=0)


def figura_variacion(d, r, archivo):
    """La variación real de cada departamento, de mayor a menor, coloreada por su tercil de pobreza."""
    t = d.sort_values("variacion_real_pct", ascending=False).reset_index(drop=True)
    n, alto = len(t), 0.36 * len(t) + 2.5
    fig = plt.figure(figsize=(8, alto), dpi=DPI, facecolor=FONDO)
    ax = fig.add_axes([1.35 / 8, 0.95 / alto, (8 - 1.35 - 0.6) / 8, (0.36 * n) / alto], facecolor=FONDO)
    ys = np.arange(n)[::-1]
    lim = max(abs(t.variacion_real_pct.min()), abs(t.variacion_real_pct.max())) * 1.18
    ax.set_xlim(min(-5, -lim), lim)
    ax.set_ylim(-0.6, n - 0.4)
    ax.barh(ys, t.variacion_real_pct, height=0.56, color=[TERCILES[c] for c in t.tercil_pobreza], zorder=3)
    for y, fila in zip(ys, t.itertuples()):
        x = fila.variacion_real_pct
        ax.text(x + (0.8 if x >= 0 else -0.8), y, f"{x:+.1f}{PCT}", va="center", ha="left" if x >= 0 else "right",
                size=8, color=TINTA["primaria"], zorder=6,   # el fondo tapa la línea nacional donde se cruzan
                bbox={"facecolor": FONDO, "edgecolor": "none", "pad": 0.8})
    ax.axvline(0, color=TINTA["base"], linewidth=1, zorder=2)
    nac = r["nacional"]["variacion_real_pct"]
    ax.axvline(nac, color=TINTA["secundaria"], linewidth=0.9, zorder=2)
    ax.set_yticks(ys, t.departamento)
    ax.grid(axis="x", color=TINTA["rejilla"], linewidth=0.8, zorder=0)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}{PCT}")
    ax.tick_params(axis="y", labelsize=9, labelcolor=TINTA["primaria"])
    ejes_limpios(ax)
    caidas = r["departamentos_con_caida_real"]
    titulo = (f"Entre {r['anio_base']} y {r['anio']} el crédito cayó en términos reales en {caidas} de "
              f"{r['n_departamentos']} departamentos; en todo el país, {nac:+.1f}{PCT}")
    lineas = encabezado(fig, titulo, f"Variación real del crédito directo del sistema financiero al sector privado, "
                        f"fin de {r['anio_base']} a fin de {r['anio']}, %",
                        f"Fuente: BCRP, crédito por departamento (series anuales RD16xxxDA, «{r['indicador']}») e "
                        f"índice de precios {r['inflacion']['codigo']} (inflación {r['inflacion']['desde']} a "
                        f"{r['inflacion']['hasta']}: {r['inflacion']['inflacion_pct']:.1f}{PCT}). Color: tercil de "
                        "pobreza monetaria 2024 (INEI, ENAHO 2024). Elaboración propia.", alto)
    fig.legend(handles=[Patch(facecolor=c, label=f"{k} 2024") for k, c in TERCILES.items()] +
               [plt.Line2D([], [], color=TINTA["secundaria"], linewidth=0.9, label=f"Perú {nac:+.1f}{PCT}")],
               loc="upper left", bbox_to_anchor=(0.25 / 8 - 0.004, 1 - (0.62 + 0.27 * lineas) / alto), ncol=4,
               frameon=False, fontsize=8.5, handlelength=1.1, labelcolor=TINTA["secundaria"])
    fig.savefig(archivo, dpi=DPI, facecolor=FONDO)
    plt.close(fig)
    t[["ccdd", "departamento", "tercil_pobreza", "pobreza_pct", "valor_base", "valor", "variacion_nominal_pct",
       "variacion_real_pct"]].round(2).to_csv(archivo.with_suffix(".csv"), index=False, encoding="utf-8")


def figura_dispersion(d, r, archivo, resaltar=None):
    """El indicador por habitante (escala logarítmica) frente a la pobreza, con los promedios nacionales."""
    alto = 7.4
    fig = plt.figure(figsize=(8, alto), dpi=DPI, facecolor=FONDO)
    ax = fig.add_axes([0.9 / 8, 0.95 / alto, (8 - 0.9 - 0.45) / 8, 4.9 / alto], facecolor=FONDO)
    ax.set_xscale("log")
    destacado = d.departamento.map(sin_tildes) == sin_tildes(resaltar) if resaltar else pd.Series(False, index=d.index)
    ax.scatter(d.por_habitante[~destacado], d.pobreza_pct[~destacado], s=46, color=PUNTO, edgecolor=FONDO,
               linewidth=1.5, zorder=3)
    if destacado.any():
        ax.scatter(d.por_habitante[destacado], d.pobreza_pct[destacado], s=70, color=RESALTE, edgecolor=FONDO,
                   linewidth=1.5, zorder=4)
    ax.set_xlim(d.por_habitante.min() * 0.8, d.por_habitante.max() * 1.3)
    ax.set_ylim(min(0, d.pobreza_pct.min() - 3), d.pobreza_pct.max() + 4)
    marcas = [m for m in [500, 1000, 2000, 3000, 5000, 10000, 20000, 30000, 50000] if ax.get_xlim()[0] <= m <= ax.get_xlim()[1]]
    ax.xaxis.set_major_locator(FixedLocator(marcas))
    ax.xaxis.set_minor_formatter(NullFormatter())
    etiquetar(fig, ax, d.por_habitante.to_numpy(), d.pobreza_pct.to_numpy(), d.departamento.tolist(), destacado.tolist())
    nac_pc = r["nacional"]["por_habitante"]
    pobreza_nac = (d.pobreza_pct * d.poblacion).sum() / d.poblacion.sum()
    ax.axvline(nac_pc, color=TINTA["base"], linewidth=0.9, zorder=1)
    ax.axhline(pobreza_nac, color=TINTA["base"], linewidth=0.9, zorder=1)
    ax.text(nac_pc * 1.03, ax.get_ylim()[1], f"Perú: S/ {nac_pc:,.0f} por habitante".replace(",", " "), size=7.5,
            color=TINTA["secundaria"], va="top")
    ax.text(d.por_habitante.min() * 0.92, pobreza_nac + 0.5, f"Perú: {pobreza_nac:.1f}{PCT} de pobreza", size=7.5,
            color=TINTA["secundaria"], va="bottom")
    ax.grid(color=TINTA["rejilla"], linewidth=0.8, zorder=0)
    ax.xaxis.set_major_formatter(lambda v, _: f"S/ {v:,.0f}".replace(",", " "))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}{PCT}")
    ax.set_xlabel(f"{r['indicador'].split(' por departamentos')[0]} por habitante, {r['anio']} (S/, escala logarítmica)",
                  size=8.5, color=TINTA["secundaria"])
    ax.set_ylabel(f"Pobreza monetaria {r['anio']}, % de la población", size=8.5, color=TINTA["secundaria"])
    ejes_limpios(ax)
    s, s2 = r["spearman_pobreza_vs_por_habitante"], r["spearman_sin_lima_callao"]
    if s["rho"] < 0 and s["p_valor"] < 0.05:
        titulo = (f"Donde hay más pobreza hay menos crédito por habitante: correlación de rangos de "
                  f"{s['rho']:.2f} entre los {s['n']} departamentos")
    else:
        titulo = (f"La correlación de rangos entre crédito por habitante y pobreza es {s['rho']:.2f} "
                  f"(valor p {s['p_valor']:.3f}) entre los {s['n']} departamentos")
    encabezado(fig, titulo, f"Crédito por habitante y pobreza monetaria por departamento, Perú {r['anio']}. "
               f"Spearman {s['rho']:.2f} (p = {s['p_valor']:.3f}); sin Lima y Callao, {s2['rho']:.2f} "
               f"(p = {s2['p_valor']:.3f})",
               f"Fuente: BCRP, crédito directo por departamento a fin de {r['anio']}; INEI, ENAHO 2024 (pobreza y "
               "población, método del INEI). Valor p por permutación (20 000 repeticiones). Asociación entre "
               "departamentos, no causalidad. Elaboración propia.", alto)
    fig.savefig(archivo, dpi=DPI, facecolor=FONDO)
    plt.close(fig)
    d[["ccdd", "departamento", "pobreza_pct", "poblacion", "valor", "por_habitante", "tercil_pobreza"]].round(2).to_csv(
        archivo.with_suffix(".csv"), index=False, encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--ipc", type=Path)
    p.add_argument("--indicadores", type=Path, default=Path("salidas/indicadores.csv"))
    p.add_argument("--resaltar", help="departamento que se destaca en la dispersión, p. ej. Piura")
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--figuras", type=Path, default=Path("figuras"))
    a = p.parse_args()
    if not a.indicadores.exists():
        raise SystemExit(f"Falta {a.indicadores.as_posix()}: usa primero la skill limpiando-enaho.")
    datos, inflacion = leer(a.panel, a.ipc, a.indicadores)
    tabla, resumen = cruzar(datos, inflacion)
    nombre = re.sub(r"[^a-z0-9]+", "_", sin_tildes(tabla.indicador.iloc[0]).split(" del ")[0].split(" en ")[0]).strip("_")
    a.salidas.mkdir(parents=True, exist_ok=True)
    a.figuras.mkdir(parents=True, exist_ok=True)
    tabla.drop(columns=["fuente", "metodo", "departamento_enaho"]).round(3).to_csv(
        a.salidas / f"cruce_{nombre}.csv", index=False, encoding="utf-8")
    resumen["archivos"] = {"tabla": f"{a.salidas.as_posix()}/cruce_{nombre}.csv", "panel_bcrp": a.panel.as_posix(),
                           "ipc_bcrp": a.ipc.as_posix() if a.ipc else None, "enaho": a.indicadores.as_posix()}
    if inflacion:
        figura_variacion(tabla, resumen, a.figuras / f"bcrp_{nombre}_real_{resumen['anio_base']}_{resumen['anio']}.png")
        resumen["archivos"]["figura_variacion"] = f"{a.figuras.as_posix()}/bcrp_{nombre}_real_{resumen['anio_base']}_{resumen['anio']}.png"
    figura_dispersion(tabla, resumen, a.figuras / f"{nombre}_vs_pobreza_{resumen['anio']}.png", a.resaltar)
    resumen["archivos"]["figura_dispersion"] = f"{a.figuras.as_posix()}/{nombre}_vs_pobreza_{resumen['anio']}.png"
    (a.salidas / f"cruce_{nombre}.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str),
                                                     encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=1, default=str))
