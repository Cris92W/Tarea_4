"""Servidor MCP del BCRP para el agente de investigación socioeconómica (Tarea 4).

Parte del proyecto de la Sesión 04, donde buscar_series venía hecha. Aquí se completan serie, resumen, los recursos y
el prompt, y se agrega una herramienta propia, panel_departamental: trae un indicador del BCRP para los 25
departamentos con el código del INEI, listo para unirse con la ENAHO por ubigeo[:2].

    uv run pytest                                           # 8 pruebas de la sesión + 2 propias: 10 passed
    uv run mcp/server.py                                    # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run mcp/server.py

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import calendar
import hashlib
import json
import re
import statistics
import time
import unicodedata
from datetime import date
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
DATOS = RAIZ / "datos" / "bcrp"          # fuera de git: el catálogo y la caché se vuelven a bajar solos
CATALOGO = DATOS / "catalogo_bcrp.csv"
CACHE = DATOS / "cache"
HORAS_CACHE = 12
MAX_PUNTOS = 1000
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
WEB = "https://estadisticas.bcrp.gob.pe/estadisticas/series"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. Para comparar departamentos "
    "usa panel_departamental, que devuelve los 25 con el código del INEI (el mismo de ubigeo[:2] en la ENAHO). "
    "No calcules a mano: cita siempre el código de la serie, el periodo y la fuente. Si una herramienta falla o no "
    "hay datos, dilo; no inventes cifras."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/bcrp/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Descripción de la serie": "descripcion",
                            "Fuente": "fuente", "Frecuencia": "frecuencia", "Fecha de actualización": "actualizada",
                            "Fecha de inicio": "inicio", "Fecha de fin": "fin"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# ------------------------------------------------------------------------------- serie y resumen (TODO 1 y 2)

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "sep": 9,
         "oct": 10, "nov": 11, "dic": 12}
CARPETA_WEB = {"Diaria": "diarias", "Mensual": "mensuales", "Trimestral": "trimestrales", "Anual": "anuales"}


def _anio(texto):
    """Los años de la API: «2025», o de dos cifras en las series diarias y trimestrales («97» es 1997)."""
    a = int(texto)
    return a if a >= 100 else a + (1900 if a >= 50 else 2000)


def _periodo(nombre, frecuencia):
    """Del periodo de la API («Ene.2025», «01.Oct.26», «T1.25», «2025») a 2025-01, 2026-10-01, 2025-T1 o 2025."""
    p = nombre.strip().split(".")
    if frecuencia == "Mensual":
        return f"{_anio(p[1])}-{MESES[p[0][:3].lower()]:02d}"
    if frecuencia == "Diaria":
        return f"{_anio(p[2])}-{MESES[p[1][:3].lower()]:02d}-{int(p[0]):02d}"
    if frecuencia == "Trimestral":
        return f"{_anio(p[1])}-{p[0].upper()}"
    return p[0]


def _fecha_api(texto, frecuencia, final=False):
    """De lo que pide el usuario (2025, 2025-03, 2025-T1, 2025-03-15) al formato de la API para esa frecuencia.

    Lo que falte se completa hacia el inicio del periodo en «desde» y hacia el final en «hasta» (final=True).
    """
    m = re.fullmatch(r"(\d{4})(?:-(T?)(\d{1,2})(?:-(\d{1,2}))?)?", str(texto).strip().upper())
    try:
        anio = int(m[1])
        if m[2]:                                          # 2025-T2: de abril a junio
            if not 1 <= int(m[3]) <= 4:
                raise ValueError
            mes = 3 * int(m[3]) if final else 3 * int(m[3]) - 2
        else:
            mes = int(m[3]) if m[3] else (12 if final else 1)
        dia = int(m[4]) if m[4] else (calendar.monthrange(anio, mes)[1] if final else 1)
        date(anio, mes, dia)                              # valida el mes y el día
    except (TypeError, ValueError):
        raise ToolError(f"Fecha no válida: {texto!r}. Usen 2025 (año), 2025-03 (mes), 2025-T1 (trimestre) "
                        "o 2025-03-15 (día).") from None
    if frecuencia == "Anual":
        return str(anio)
    if frecuencia == "Trimestral":
        return f"{anio}-{(mes - 1) // 3 + 1}"
    if frecuencia == "Mensual":
        return f"{anio}-{mes}"
    return f"{anio}-{mes:02d}-{dia:02d}"


def _orden(fecha_api):
    return tuple(int(x) for x in fecha_api.split("-"))


def _inicio_api(inicio, frecuencia):
    """La fecha de inicio del catálogo («Ene-1950», «T1-2005», «1997-01-02», «2004») en el formato de la API."""
    if m := re.fullmatch(r"([A-Za-z]{3})-(\d{4})", inicio.strip()):
        return f"{m[2]}-{MESES[m[1].lower()]}"
    if m := re.fullmatch(r"T(\d)-(\d{4})", inicio.strip()):
        return f"{m[2]}-{m[1]}"
    return _fecha_api(inicio, frecuencia)


def _api(codigos, desde, hasta):
    """Pide una o varias series (separadas por guiones) a la API del BCRP y guarda la respuesta 12 horas en caché.

    Con muchos pedidos seguidos, o con un rango sin datos, la API responde una página HTML en vez de JSON: se espera
    y se reintenta, y si sigue así se avisa con un error explícito.
    """
    url = f"{API}/{'-'.join(codigos)}/json/{desde}/{hasta}"
    archivo = CACHE / f"{hashlib.sha1(url.encode()).hexdigest()[:16]}.json"
    if archivo.exists() and time.time() - archivo.stat().st_mtime < HORAS_CACHE * 3600:
        return json.loads(archivo.read_text(encoding="utf-8")), url
    for espera in (0, 2, 5, 10):
        time.sleep(espera)
        try:
            r = httpx.get(url, timeout=60, follow_redirects=True)
            r.raise_for_status()
            respuesta = r.json()
            break
        except (httpx.HTTPError, ValueError):
            continue
    else:
        raise ToolError(f"El BCRP no respondió con datos para {', '.join(codigos)} entre {desde} y {hasta} ({url}). "
                        "O no hay datos en ese rango, o la API está limitando los pedidos: revisen el rango y "
                        "reintenten en unos segundos.")
    CACHE.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(respuesta, ensure_ascii=False), encoding="utf-8")
    return respuesta, url


def _valor(texto):
    try:
        return float(texto)
    except (TypeError, ValueError):                       # «n.d.»
        return None


def _serie(codigo, desde, hasta):
    f = _ficha(codigo)
    d, h = _fecha_api(desde, f["frecuencia"]), _fecha_api(hasta, f["frecuencia"], final=True)
    if _orden(h) < _orden(d):
        raise ToolError(f"El periodo está al revés: «desde» ({desde}) es posterior a «hasta» ({hasta}).")
    try:
        antes_del_inicio = _orden(h) < _orden(_inicio_api(f["inicio"], f["frecuencia"]))
    except (ToolError, KeyError, ValueError):             # un inicio con otro formato no impide consultar
        antes_del_inicio = False
    if antes_del_inicio:
        raise ToolError(f"La serie {codigo} empieza en {f['inicio']}: no hay datos hasta {hasta}.")
    respuesta, url = _api([codigo], d, h)
    datos = [{"periodo": _periodo(p["name"], f["frecuencia"]), "valor": v}
             for p in respuesta.get("periods", []) if (v := _valor(p["values"][0])) is not None]
    salida = f | {"datos": datos, "fuente": url,
                  "fuente_web": f"{WEB}/{CARPETA_WEB[f['frecuencia']]}/resultados/{codigo}/html/{d}/{h}/"}
    if not datos:
        salida["nota"] = (f"El BCRP no tiene datos publicados de {codigo} entre {desde} y {hasta} (la serie empieza "
                          f"en {f['inicio']}; el catálogo se actualizó el {f['actualizada']}).")
    return salida


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str | int, hasta: str | int) -> dict:
    """Descarga los datos oficiales de una serie del BCRP entre dos fechas.

    codigo: el que da buscar_series, p. ej. "PN01273PM" (inflación de Lima a 12 meses).
    desde / hasta: "2025" (año), "2025-03" (mes), "2025-T1" (trimestre) o "2026-10-15" (día); se ajustan a la
    frecuencia de la serie. Devuelve los datos como [{"periodo": "2025-03", "valor": 0.81}] (sin los «n.d.»), el
    enlace a la API usada (fuente) y el de la tabla en la web del BCRP para verificarlos (fuente_web).
    Para variaciones, promedios o extremos usen resumen en vez de calcular con estos datos.
    """
    s = _serie(codigo, desde, hasta)
    if len(s["datos"]) > MAX_PUNTOS:
        s["nota"] = (f"Son {len(s['datos'])} datos; se muestran los últimos {MAX_PUNTOS}. Para todo el periodo "
                     "usen resumen o acorten el rango.")
        s["datos"] = s["datos"][-MAX_PUNTOS:]
    return s


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str | int, hasta: str | int) -> dict:
    """Resume una serie del BCRP en un periodo, con las cuentas hechas en Python.

    Devuelve el primer y el último dato, el cambio entre ambos (en la unidad de la serie), la variación porcentual,
    el promedio y el máximo y el mínimo con su periodo, más las fuentes. Úsenla en vez de calcular a mano. Si la
    serie ya es una tasa (p. ej. la inflación en %), «cambio» está en puntos porcentuales y «variacion_pct» es el
    cambio relativo de esa tasa. Para la inflación acumulada de un periodo usen el índice de precios (no la tasa):
    su variacion_pct entre el mes base y el mes final es la inflación acumulada.
    """
    s = _serie(codigo, desde, hasta)
    datos = s["datos"]
    if not datos:
        raise ToolError(s["nota"])
    primero, ultimo = datos[0], datos[-1]
    return {"codigo": s["codigo"], "nombre": s["nombre"], "frecuencia": s["frecuencia"],
            "desde": primero["periodo"], "hasta": ultimo["periodo"], "n": len(datos),
            "primero": primero, "ultimo": ultimo,
            "cambio": round(ultimo["valor"] - primero["valor"], 6),
            "variacion_pct": round((ultimo["valor"] / primero["valor"] - 1) * 100, 4) if primero["valor"] else None,
            "promedio": round(statistics.fmean(x["valor"] for x in datos), 6),
            "maximo": max(datos, key=lambda x: x["valor"]), "minimo": min(datos, key=lambda x: x["valor"]),
            "fuente": s["fuente"], "fuente_web": s["fuente_web"]}


# ------------------------------------------------------------ herramienta propia: panel_departamental (TODO 3)

# Los códigos del INEI: los dos primeros dígitos del ubigeo en la ENAHO y FIRST_IDDP en el GeoJSON del curso
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
CCDD = {_sin_tildes(n): c for c, n in DEPARTAMENTOS.items()} | {"cuzco": "08"}
SINONIMOS = {"pbi": "producto bruto interno", "spp": "sistema privado de pensiones",
             "afp": "sistema privado de pensiones", "igv": "impuesto general a las ventas"}
VACIAS = {"de", "del", "la", "las", "el", "los", "por", "en", "y", "a", "al", "segun"}
VARIANTES_PREFERIDAS = ["total", "millones de soles", "gwh", ""]


def _normal(s):
    return " ".join(_sin_tildes(s).split())


@cache
def _regionales():
    """Las series anuales de la «Información estadística regional» del BCRP, con su lugar y su variante."""
    df = catalogo()
    reg = df[df.descripcion.str.startswith("Información estadística regional") & (df.frecuencia == "Anual")].copy()
    partes = reg.nombre.str.strip().str.extract(r"^(.*?)\s*(?:\((.*)\))?$")
    reg["lugar"] = partes[0].str.strip()
    reg["variante"] = partes[1].fillna("").str.strip()
    reg["ccdd"] = reg.lugar.map(lambda s: CCDD.get(_normal(s)))
    return reg


@cache
def _grupos_departamentales():
    """Los indicadores que el BCRP publica para al menos 20 de los 25 departamentos."""
    reg = _regionales()
    g = reg[reg.ccdd.notna()].groupby("grupo").agg(
        categoria=("categoria", "first"), departamentos=("ccdd", "nunique"),
        variantes=("variante", lambda s: sorted(set(s))), desde=("inicio", "min"), hasta=("fin", "max"))
    return g[g.departamentos >= 20]


def _grupo(indicador):
    texto = _normal(indicador)
    for corto, largo in SINONIMOS.items():
        texto = re.sub(rf"\b{corto}\b", largo, texto)
    grupos = _grupos_departamentales()
    nombres = grupos.index.map(_normal)
    elegidos = [g for g, n in zip(grupos.index, nombres)
                if all(p in n for p in texto.split() if p not in VACIAS)]
    elegidos.sort(key=lambda g: (-grupos.departamentos[g], len(g)))
    if not texto.strip() or not elegidos:
        raise ToolError(f"El BCRP no publica por departamento un indicador que coincida con {indicador!r}. "
                        f"Los disponibles son: {'; '.join(grupos.index)}.")
    return elegidos[0], elegidos[1:6]


def _variacion(valor, base):
    return round((valor / base - 1) * 100, 4) if valor is not None and base else None


def _extremo(x):
    return {"ccdd": x["ccdd"], "departamento": x["departamento"], "valor": x["valor"]}


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True})
def panel_departamental(indicador: str, anio: int, anio_base: int | None = None, variante: str | None = None,
                        guardar: bool = False) -> dict:
    """Trae un indicador anual del BCRP para los 25 departamentos del Perú, con el código del INEI de cada uno.

    Sirve para comparar territorios y para unir el BCRP con la ENAHO o con un mapa: «ccdd» es el mismo código que
    ubigeo[:2] en la ENAHO y que FIRST_IDDP en el GeoJSON del curso. Lima (15) y Callao (07) van separados.

    indicador: palabras del indicador, p. ej. "credito directo", "depositos", "gasto gobiernos regionales",
    "gasto gobiernos locales", "inversion gobierno nacional", "afiliados spp" o "pbi constantes". La lista
    completa está en el recurso bcrp://indicadores-departamentales.
    anio: el año que se compara, p. ej. 2024. anio_base: otro año, para la variación % de cada departamento.
    variante: cuando el indicador tiene varias, p. ej. "moneda nacional" o "var% anual"; por defecto, el total.
    guardar: True escribe la tabla en salidas/bcrp/ como CSV, para unirla con otros datos sin copiar cifras a mano.

    Devuelve cada departamento con su valor y su puesto (1 = el mayor), el total nacional si el BCRP lo publica, el
    promedio, la mediana, el máximo y el mínimo, los enlaces a la fuente y qué departamentos faltan, si falta alguno.
    """
    grupo, alternativas = _grupo(indicador)
    reg = _regionales()
    sub = reg[reg.grupo == grupo]
    disponibles = sorted(set(sub.variante))
    if variante:
        elegidas = [v for v in disponibles if _normal(variante) in _normal(v)]
        if not elegidas:
            raise ToolError(f"«{grupo}» no tiene la variante {variante!r}. Tiene: {disponibles}.")
        var = elegidas[0]
    else:
        var = next((v for p in VARIANTES_PREFERIDAS for v in disponibles if _normal(v) == p), disponibles[0])
    sub = sub[sub.variante == var]
    deps = sub[sub.ccdd.notna()].drop_duplicates("ccdd")
    es_total = sub.lugar.map(_normal) == "total"
    total = sub[es_total]
    otras = sorted(set(sub.lugar[sub.ccdd.isna() & ~es_total]))

    # La API devuelve las series ordenadas por código, no en el orden pedido: se piden ordenadas y se verifica
    codigos = sorted(set(deps.codigo) | set(total.codigo))
    desde = min(anio, anio_base or anio)
    respuesta, url = _api(codigos, str(desde), str(anio))
    nombres = dict(zip(sub.codigo, sub.nombre))
    devueltas = [s["name"] for s in respuesta.get("config", {}).get("series", [])]
    if len(devueltas) != len(codigos) or not all(
            _normal(d).endswith(_normal(nombres[c])) for c, d in zip(codigos, devueltas)):
        raise ToolError(f"La API del BCRP devolvió las series de «{grupo}» en un orden inesperado ({url}); "
                        "no se asignan valores a ciegas.")
    valores = {c: {} for c in codigos}
    for p in respuesta.get("periods", []):
        for c, v in zip(codigos, p["values"]):
            valores[c][p["name"]] = _valor(v)

    filas, faltantes = [], []
    for ccdd, nombre in DEPARTAMENTOS.items():
        fila = deps[deps.ccdd == ccdd]
        if fila.empty:
            faltantes.append(nombre)
            continue
        c = fila.codigo.iloc[0]
        x = {"ccdd": ccdd, "departamento": nombre, "codigo": c, "valor": valores[c].get(str(anio))}
        if anio_base:
            base = valores[c].get(str(anio_base))
            x |= {"valor_base": base, "variacion_pct": _variacion(x["valor"], base)}
        filas.append(x)
    con_dato = [x for x in filas if x["valor"] is not None]
    if not con_dato:
        raise ToolError(f"El BCRP no tiene publicado «{grupo}» para {anio}. Según el catálogo hay datos de "
                        f"{_grupos_departamentales().desde[grupo]} a {_grupos_departamentales().hasta[grupo]}.")
    for puesto, x in enumerate(sorted(con_dato, key=lambda x: -x["valor"]), 1):
        x["puesto"] = puesto
    valores_anio = [x["valor"] for x in con_dato]

    total_nacional = None
    if not total.empty:
        c = total.codigo.iloc[0]
        total_nacional = {"codigo": c, "valor": valores[c].get(str(anio))}
        if anio_base:
            base = valores[c].get(str(anio_base))
            total_nacional |= {"valor_base": base, "variacion_pct": _variacion(total_nacional["valor"], base)}
    unidad = var if var not in ("", "total", "moneda nacional", "moneda extranjera") else (
        m[1] if (m := re.search(r"\(([^()]*)\)\s*$", grupo)) else "")
    salida = {
        "indicador": grupo, "variante": var or None, "unidad": unidad, "anio": anio, "anio_base": anio_base,
        "departamentos": filas, "total_nacional": total_nacional,
        "resumen": {"n": len(con_dato), "promedio": round(statistics.fmean(valores_anio), 4),
                    "mediana": round(statistics.median(valores_anio), 4),
                    "maximo": _extremo(max(con_dato, key=lambda x: x["valor"])),
                    "minimo": _extremo(min(con_dato, key=lambda x: x["valor"]))},
        "faltantes": faltantes, "otras_unidades": otras, "alternativas": alternativas,
        "fuente": url, "fuente_web": f"{WEB}/anuales/resultados/{'-'.join(codigos)}/html/{desde}/{anio}/",
        "nota": "ccdd es el código del INEI (ubigeo[:2] en la ENAHO, FIRST_IDDP en el mapa). Los valores son "
                "nominales y del año calendario; para compararlos entre años consideren la inflación."}
    if guardar:
        sufijo = f"{anio}" + (f"_{anio_base}" if anio_base else "")
        nombre = re.sub(r"[^a-z0-9]+", "_", _normal(grupo)).strip("_")[:60]
        destino = RAIZ / "salidas" / "bcrp" / f"panel_{nombre}_{sufijo}.csv"
        destino.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(filas).assign(indicador=grupo, unidad=unidad, anio=anio, fuente=url).to_csv(
            destino, index=False, encoding="utf-8")
        salida["archivo"] = destino.relative_to(RAIZ).as_posix()
    return salida


# --------------------------------------------------------------------------- recursos (TODO 4) y prompt (TODO 5)

def _json(x):
    return json.dumps(x, ensure_ascii=False, indent=1)


@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha_serie(codigo: str) -> str:
    """La ficha de una serie del BCRP: nombre, frecuencia, desde cuándo hay datos, fuente original y enlaces."""
    f = _ficha(codigo)
    fila = catalogo().query("codigo == @codigo").iloc[0]
    extra = {"descripcion": fila.descripcion} if fila.descripcion else {}
    return _json(f | {"fuente_original": fila.fuente} | extra | {
        "api": f"{API}/{codigo}/json", "web": f"{WEB}/{CARPETA_WEB[f['frecuencia']]}/resultados/{codigo}/html"})


@mcp.resource("bcrp://indicadores-departamentales", mime_type="application/json")
def indicadores_departamentales() -> str:
    """Los indicadores anuales que el BCRP publica por departamento y que acepta panel_departamental."""
    return _json([{"indicador": grupo, "categoria": r.categoria, "departamentos": int(r.departamentos),
                   "variantes": [v or "(única)" for v in r.variantes], "desde": r.desde, "hasta": r.hasta}
                  for grupo, r in _grupos_departamentales().iterrows()])


@mcp.prompt
def informe(tema: str, desde: str = "2020", hasta: str = "2024") -> str:
    """Pide un informe breve con cifras oficiales del BCRP, cada una con su código de serie, periodo y fuente."""
    return (f"Prepara un informe breve sobre «{tema}» en el Perú entre {desde} y {hasta}, solo con datos oficiales "
            "del BCRP obtenidos con las herramientas del servidor bcrp.\n\n"
            "1. Busca las series pertinentes con buscar_series y elige las de frecuencia adecuada.\n"
            "2. Obtén las cifras con resumen (variaciones, promedio, extremos) o con serie; para comparar "
            "departamentos usa panel_departamental. No hagas cuentas a mano.\n"
            "3. Cada cifra va con su código de serie, su periodo y su fuente (el enlace que devuelve la herramienta).\n"
            "4. Si una serie no existe, no tiene datos o una herramienta falla, dilo y no estimes el valor.\n"
            "5. Describe asociaciones sin presentarlas como causas.\n\n"
            "Formato: un párrafo de contexto, una tabla «indicador | código | periodo | valor | fuente», tres "
            "hallazgos y una sección de limitaciones.")


if __name__ == "__main__":
    mcp.run()
