"""Limpia los módulos 34 (sumaria) y 02 (miembros del hogar) de la ENAHO y arma una base de residentes habituales.

    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py              # ENAHO 2024, desde datos/enaho/

El orden no se discute: leer, normalizar, filtrar residentes habituales, unir personas y hogares (m:1), construir
los indicadores, validar y guardar. Si una validación esencial falla, la base NO se guarda y el script termina con
error: nunca se corrigen resultados para que calcen con la referencia.

Dos ponderaciones, cada una para su unidad de análisis:
- Pobreza de un territorio o de un tipo de hogar: la sumaria con factor07 × mieperho (el método del INEI; cada
  hogar representa a factor07 hogares de mieperho miembros). Es la que reproduce las cifras oficiales.
- Pobreza según un rasgo de la persona (sexo, edad): los residentes habituales con facpob07.

Salidas, en salidas/:
  personas_2024.parquet   una fila por residente habitual: hogar, departamento, área, sexo, edad, pobreza y factores
  hogares_2024.parquet    una fila por hogar de la sumaria, con peso_inei = factor07 × mieperho
  validacion.txt          cada verificación con APROBADA o FALLIDA, lo obtenido y lo esperado
  indicadores.csv         pobreza ponderada: nacional, área, dominio, departamento, sexo del jefe, sexo y edad
"""
import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ARCHIVOS = {2024: {"sumaria": ("966-Modulo34.zip", "sumaria-2024.dta"),
                   "personas": ("966-Modulo02.zip", "enaho01-2024-200.dta")}}
# Cifras publicadas de la ENAHO 2024 (issue #201 y Sesión 16): solo se comparan, nunca pasan a los resultados
REFERENCIA = {"pobreza": 27.6, "residentes": 108_664, "departamentos": 25, "urbana": 24.8, "rural": 39.3,
              "extrema": 5.5, "lima_metropolitana": 28.2}
TOLERANCIA = 0.1            # puntos porcentuales: la diferencia máxima que acepta el issue para la pobreza nacional
LLAVES = ["conglome", "vivienda", "hogar"]
ANCHOS = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
DOMINIOS = {1: "Costa norte", 2: "Costa centro", 3: "Costa sur", 4: "Sierra norte", 5: "Sierra centro",
            6: "Sierra sur", 7: "Selva", 8: "Lima Metropolitana"}
GRUPOS_EDAD = {"0 a 14": (0, 14), "15 a 29": (15, 29), "30 a 44": (30, 44), "45 a 64": (45, 64), "65 y más": (65, 200)}
SUMARIA = LLAVES + ["ubigeo", "dominio", "estrato", "mieperho", "pobreza", "factor07", "gashog2d", "linea", "linpe"]
PERSONAS = LLAVES + ["codperso", "ubigeo", "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]
HOGARES_INEI = "hogares: factor07 × mieperho (INEI)"
PERSONAS_FACPOB = "personas residentes: facpob07"


def normalizar(nombre):
    """Minúsculas y sin espacios; la «ñ» pasa a «ni», así «aÑo» queda «anio»."""
    return nombre.strip().lower().replace("ñ", "ni")


def leer(carpeta, archivo_zip, miembro):
    """Lee un .dta dentro del zip del INEI sin convertir categorías, con las llaves como texto de ancho fijo."""
    with zipfile.ZipFile(carpeta / archivo_zip) as z:
        nombre = next(n for n in z.namelist() if n.lower().endswith(miembro.lower()))
        with z.open(nombre) as f:
            df = pd.read_stata(f, convert_categoricals=False)
    df.columns = [normalizar(c) for c in df.columns]
    for llave, ancho in ANCHOS.items():
        if llave in df.columns:     # vienen como texto en el .dta; se fuerza por si una versión las trae numéricas
            df[llave] = df[llave].astype(str).str.strip().str.split(".").str[0].str.zfill(ancho)
    return df, nombre


def tasa(df, columna, peso):
    """Porcentaje ponderado: suma de pesos de quienes cumplen / suma de pesos."""
    return 100 * (df[columna] * df[peso]).sum() / df[peso].sum()


def miles(x):
    return f"{x:,.0f}".replace(",", " ")


class Validacion:
    def __init__(self):
        self.filas = []

    def revisar(self, nombre, ok, obtenido, esperado="", esencial=True):
        self.filas.append({"ok": bool(ok), "esencial": esencial, "nombre": nombre, "obtenido": obtenido,
                           "esperado": esperado})

    @property
    def fallidas_esenciales(self):
        return [f for f in self.filas if f["esencial"] and not f["ok"]]

    def escribir(self, ruta, encabezado, pie):
        lineas = encabezado + [""]
        for f in self.filas:
            estado = "APROBADA" if f["ok"] else "FALLIDA "
            tipo = "esencial" if f["esencial"] else "control "
            esperado = f" | esperado: {f['esperado']}" if f["esperado"] != "" else ""
            lineas.append(f"[{estado}] ({tipo}) {f['nombre']}: {f['obtenido']}{esperado}")
        aprobadas = sum(f["ok"] for f in self.filas)
        lineas += ["", f"Resultado: {aprobadas} aprobadas, {len(self.filas) - aprobadas} fallidas "
                       f"({len(self.fallidas_esenciales)} esenciales fallidas)."] + pie
        ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def limpiar(anio=2024, datos=Path("datos/enaho"), salidas=Path("salidas")):
    if anio not in ARCHIVOS:
        raise SystemExit(f"Solo está configurada la ENAHO {sorted(ARCHIVOS)}.")
    faltan = [z for z, _ in ARCHIVOS[anio].values() if not (datos / z).exists()]
    if faltan:
        raise SystemExit(f"Faltan {faltan} en {datos.as_posix()}/. Bájenlos con: "
                         "uv run .claude/skills/limpiando-enaho/scripts/descargar.py")
    v = Validacion()

    # 1. Leer y 2. normalizar
    sumaria, nombre_s = leer(datos, *ARCHIVOS[anio]["sumaria"])
    modulo02, nombre_p = leer(datos, *ARCHIVOS[anio]["personas"])
    n_hogares, n_filas = len(sumaria), len(modulo02)
    sumaria, modulo02 = sumaria[SUMARIA].copy(), modulo02[PERSONAS].copy()
    sumaria["factor07"] = sumaria.factor07.astype("float64")          # vienen en float32: se suman en float64
    modulo02["facpob07"] = modulo02.facpob07.astype("float64")
    v.revisar("Llaves con sus ceros iniciales (conglome 6, vivienda 3, hogar 2, codperso 2, ubigeo 6 dígitos)",
              all(df[k].str.fullmatch(rf"\d{{{a}}}").all() for df in (sumaria, modulo02)
                  for k, a in ANCHOS.items() if k in df), "todas de ancho fijo y solo dígitos")
    duplicados = sumaria.duplicated(LLAVES).sum()
    v.revisar("Llaves de hogar únicas en la sumaria (conglome, vivienda, hogar)", duplicados == 0,
              f"{miles(n_hogares)} hogares, {duplicados} duplicados", "0 duplicados")
    duplicados = modulo02.duplicated(LLAVES + ["codperso"]).sum()
    v.revisar("Llaves de persona únicas en el módulo 02 (+ codperso)", duplicados == 0,
              f"{miles(n_filas)} filas, {duplicados} duplicados", "0 duplicados")

    # 3. Filtrar residentes habituales (la condición de la Sesión 16)
    residente = ((modulo02.p204 == 1) & (modulo02.p205 == 2)) | ((modulo02.p204 == 2) & (modulo02.p206 == 1))
    personas = modulo02[residente].copy()
    v.revisar("Residentes habituales: ((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))",
              len(personas) == REFERENCIA["residentes"], f"{miles(len(personas))} de {miles(n_filas)} filas",
              miles(REFERENCIA["residentes"]))

    # 4. Unir personas y hogares: cada persona con un solo hogar
    sumaria["pobre"] = sumaria.pobreza <= 2
    sumaria["pobre_extremo"] = sumaria.pobreza == 1
    jefes = modulo02.loc[modulo02.p203 == 1, LLAVES + ["p207"]]       # del módulo completo: el jefe puede estar ausente
    sumaria = sumaria.merge(jefes.rename(columns={"p207": "sexo_jefe"}), on=LLAVES, how="left", validate="1:1")
    sumaria["sexo_jefe"] = sumaria.sexo_jefe.map({1: "Hombre", 2: "Mujer"})
    v.revisar("Cada hogar de la sumaria tiene un solo jefe o jefa en el módulo 02 (merge 1:1)",
              sumaria.sexo_jefe.notna().all(), f"{int(sumaria.sexo_jefe.isna().sum())} hogares sin jefe", "0")
    antes = len(personas)
    base = personas.merge(sumaria, on=LLAVES, how="left", validate="m:1", indicator=True, suffixes=("", "_hogar"))
    sin_hogar = (base._merge != "both").sum()
    v.revisar("Unión personas-hogares con merge(validate='m:1') sin duplicar ni perder filas",
              len(base) == antes and sin_hogar == 0,
              f"{miles(antes)} filas antes, {miles(len(base))} después, {sin_hogar} personas sin hogar", "iguales y 0")
    distinto = (base.ubigeo != base.ubigeo_hogar).sum()
    v.revisar("El ubigeo de cada persona coincide con el de su hogar", distinto == 0, f"{distinto} diferencias", "0",
              esencial=False)
    base = base.drop(columns=["_merge", "ubigeo_hogar"])

    # 5. Construir indicadores: departamento, área, dominio, sexo, edad y pobreza
    for df in (base, sumaria):
        df["ccdd"] = df.ubigeo.str[:2]
        df["departamento"] = df.ccdd.map(DEPARTAMENTOS)
        df["dominio_nombre"] = df.dominio.map(DOMINIOS)
        df["area"] = np.where(df.estrato <= 5, "Urbana", "Rural")
    sumaria["peso_inei"] = sumaria.factor07 * sumaria.mieperho        # personas que representa cada hogar
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(base.edad, [-1] + [b for _, b in GRUPOS_EDAD.values()], labels=list(GRUPOS_EDAD))
    base["gasto_pc_mensual"] = base.gashog2d / (12 * base.mieperho)
    codigos = sorted(base.ccdd.unique())
    v.revisar("Códigos territoriales ubigeo[:2]: los 25 departamentos del INEI, cada uno con nombre",
              codigos == sorted(DEPARTAMENTOS) and base.departamento.notna().all()
              and sorted(sumaria.ccdd.unique()) == codigos,
              f"{len(codigos)} códigos ({codigos[0]} a {codigos[-1]}) en personas y en hogares", "25 (01 a 25)")
    faltantes = int(base[["sexo", "edad", "facpob07"]].isna().any(axis=1).sum())
    v.revisar("Cada residente tiene sexo, edad y factor de expansión", faltantes == 0,
              f"{faltantes} personas con datos faltantes", "0")

    # 6. Validar con los factores de expansión
    pob_personas, pob_hogares = base.facpob07.sum(), sumaria.peso_inei.sum()
    v.revisar("Factores de expansión positivos y sin nulos (facpob07 y factor07)",
              (base.facpob07 > 0).all() and (sumaria.factor07 > 0).all(),
              f"facpob07 suma {miles(pob_personas)} personas; factor07 suma {miles(sumaria.factor07.sum())} hogares")
    v.revisar("La población expandida con personas y con la sumaria difiere menos de 1 %",
              abs(pob_personas / pob_hogares - 1) < 0.01,
              f"{miles(pob_personas)} (facpob07) frente a {miles(pob_hogares)} (factor07 × mieperho)", "< 1 %")
    nacional_inei, nacional_personas = tasa(sumaria, "pobre", "peso_inei"), tasa(base, "pobre", "facpob07")
    v.revisar(f"Pobreza monetaria nacional, método del INEI: sumaria con factor07 × mieperho (tolerancia {TOLERANCIA} pp)",
              abs(nacional_inei - REFERENCIA["pobreza"]) <= TOLERANCIA, f"{nacional_inei:.2f} %",
              f"{REFERENCIA['pobreza']} %")
    v.revisar(f"Pobreza monetaria nacional, residentes ponderados con facpob07 (tolerancia {TOLERANCIA} pp)",
              abs(nacional_personas - REFERENCIA["pobreza"]) <= TOLERANCIA, f"{nacional_personas:.2f} %",
              f"{REFERENCIA['pobreza']} %")
    sin_peso = 100 * base.pobre.mean()
    v.revisar("Sin ponderar la cifra cambia (por eso se pondera)", abs(sin_peso - nacional_personas) > TOLERANCIA,
              f"promedio simple {sin_peso:.2f} % frente a {nacional_personas:.2f} % ponderado", esencial=False)
    for clave, nombre, h, p in [
            ("urbana", "Pobreza urbana (estrato <= 5)", sumaria.area == "Urbana", base.area == "Urbana"),
            ("rural", "Pobreza rural (estrato >= 6)", sumaria.area == "Rural", base.area == "Rural"),
            ("lima_metropolitana", "Pobreza en Lima Metropolitana (dominio 8)", sumaria.dominio == 8,
             base.dominio == 8)]:
        x = tasa(sumaria[h], "pobre", "peso_inei")
        v.revisar(f"{nombre}, método del INEI", abs(x - REFERENCIA[clave]) <= TOLERANCIA,
                  f"{x:.2f} % (con facpob07: {tasa(base[p], 'pobre', 'facpob07'):.2f} %)",
                  f"{REFERENCIA[clave]} %", esencial=False)
    extrema = tasa(sumaria, "pobre_extremo", "peso_inei")
    v.revisar("Pobreza extrema nacional (pobreza == 1), método del INEI", abs(extrema - REFERENCIA["extrema"]) <= TOLERANCIA,
              f"{extrema:.2f} %", f"{REFERENCIA['extrema']} %", esencial=False)
    concuerda = 100 * ((sumaria.gashog2d / (12 * sumaria.mieperho) < sumaria.linea) == sumaria.pobre).mean()
    v.revisar("La variable pobreza concuerda con gasto per cápita mensual < línea de pobreza", concuerda >= 99,
              f"{concuerda:.2f} % de los hogares", ">= 99 %", esencial=False)

    # 7. Guardar, solo si todas las validaciones esenciales pasaron
    salidas.mkdir(parents=True, exist_ok=True)
    parquet, parquet_hogares = salidas / f"personas_{anio}.parquet", salidas / f"hogares_{anio}.parquet"
    encabezado = [f"VALIDACIÓN · ENAHO {anio} (INEI), módulos 34 (sumaria) y 02 (miembros del hogar)",
                  f"Generado por .claude/skills/limpiando-enaho/scripts/limpiar.py el {datetime.now():%Y-%m-%d %H:%M}",
                  f"Sumaria:  {datos.as_posix()}/{ARCHIVOS[anio]['sumaria'][0]} → {nombre_s} ({miles(n_hogares)} hogares)",
                  f"Personas: {datos.as_posix()}/{ARCHIVOS[anio]['personas'][0]} → {nombre_p} ({miles(n_filas)} filas)",
                  "Esencial: si falla, la base no se guarda. Control: se informa, pero no detiene el proceso."]
    if v.fallidas_esenciales:
        parquet.unlink(missing_ok=True)
        parquet_hogares.unlink(missing_ok=True)
        v.escribir(salidas / "validacion.txt", encabezado, ["NO se guardó la base: falló una validación esencial."])
        nombres = "; ".join(f["nombre"] for f in v.fallidas_esenciales)
        raise SystemExit(f"VALIDACIÓN FALLIDA ({nombres}). Detalle en {salidas.as_posix()}/validacion.txt")
    columnas = ["conglome", "vivienda", "hogar", "codperso", "ubigeo", "ccdd", "departamento", "dominio",
                "dominio_nombre", "estrato", "area", "p203", "sexo", "sexo_jefe", "edad", "grupo_edad", "mieperho",
                "pobreza", "pobre", "pobre_extremo", "gasto_pc_mensual", "linea", "linpe", "factor07", "facpob07"]
    base[columnas].to_parquet(parquet, index=False)
    sumaria["gasto_pc_mensual"] = sumaria.gashog2d / (12 * sumaria.mieperho)
    sumaria[["conglome", "vivienda", "hogar", "ubigeo", "ccdd", "departamento", "dominio", "dominio_nombre",
             "estrato", "area", "sexo_jefe", "mieperho", "pobreza", "pobre", "pobre_extremo", "gasto_pc_mensual",
             "linea", "linpe", "factor07", "peso_inei"]].to_parquet(parquet_hogares, index=False)
    tabla = indicadores(base, sumaria)
    tabla.to_csv(salidas / "indicadores.csv", index=False, encoding="utf-8")
    v.escribir(salidas / "validacion.txt", encabezado,
               [f"Base guardada: {parquet.as_posix()} ({miles(len(base))} residentes habituales, {len(columnas)} columnas).",
                f"Base de hogares: {parquet_hogares.as_posix()} ({miles(len(sumaria))} hogares, con peso_inei).",
                f"Indicadores ponderados: {salidas.as_posix()}/indicadores.csv ({len(tabla)} filas).",
                f"Pobreza nacional {anio}: {nacional_inei:.2f} % con el método del INEI; "
                f"{nacional_personas:.2f} % con residentes y facpob07."])
    print((salidas / "validacion.txt").read_text(encoding="utf-8"))
    return parquet


def indicadores(base, sumaria):
    """La tabla de pobreza ponderada que usan las Skills de gráficos y mapas y el agente."""
    filas = []

    def por_hogares(nivel, categoria, h, p, codigo=""):
        filas.append({"nivel": nivel, "codigo": codigo, "categoria": categoria, "metodo": HOGARES_INEI,
                      "pobreza_pct": tasa(h, "pobre", "peso_inei"),
                      "pobreza_extrema_pct": tasa(h, "pobre_extremo", "peso_inei"),
                      "pobreza_pct_facpob07": tasa(p, "pobre", "facpob07"),
                      "poblacion": h.peso_inei.sum(), "pobres": (h.peso_inei * h.pobre).sum(),
                      "n_hogares": len(h), "n_personas": len(p)})

    def por_personas(nivel, categoria, p):
        filas.append({"nivel": nivel, "codigo": "", "categoria": categoria, "metodo": PERSONAS_FACPOB,
                      "pobreza_pct": tasa(p, "pobre", "facpob07"),
                      "pobreza_extrema_pct": tasa(p, "pobre_extremo", "facpob07"),
                      "pobreza_pct_facpob07": tasa(p, "pobre", "facpob07"),
                      "poblacion": p.facpob07.sum(), "pobres": (p.facpob07 * p.pobre).sum(),
                      "n_hogares": len(p[LLAVES].drop_duplicates()), "n_personas": len(p)})

    por_hogares("nacional", "Perú", sumaria, base)
    for area in ["Urbana", "Rural"]:
        por_hogares("area", area, sumaria[sumaria.area == area], base[base.area == area])
    for codigo, nombre in DOMINIOS.items():
        por_hogares("dominio", nombre, sumaria[sumaria.dominio == codigo], base[base.dominio == codigo], str(codigo))
    for ccdd, nombre in DEPARTAMENTOS.items():
        por_hogares("departamento", nombre, sumaria[sumaria.ccdd == ccdd], base[base.ccdd == ccdd], ccdd)
    for sexo, nombre in [("Hombre", "Jefe hombre"), ("Mujer", "Jefa mujer")]:
        por_hogares("sexo_jefe_hogar", nombre, sumaria[sumaria.sexo_jefe == sexo], base[base.sexo_jefe == sexo])
    for sexo in ["Hombre", "Mujer"]:
        por_personas("sexo", sexo, base[base.sexo == sexo])
    for grupo in GRUPOS_EDAD:
        por_personas("grupo_edad", grupo, base[base.grupo_edad == grupo])
    tabla = pd.DataFrame(filas)
    total = {HOGARES_INEI: (sumaria.peso_inei * sumaria.pobre).sum(), PERSONAS_FACPOB: (base.facpob07 * base.pobre).sum()}
    tabla["pobres_pct_del_total"] = 100 * tabla.pobres / tabla.metodo.map(total)
    return tabla.round({"pobreza_pct": 2, "pobreza_extrema_pct": 2, "pobreza_pct_facpob07": 2, "poblacion": 0,
                        "pobres": 0, "pobres_pct_del_total": 2})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")     # la consola de Windows usa cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--datos", type=Path, default=Path("datos/enaho"))
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    a = p.parse_args()
    try:
        limpiar(a.anio, a.datos, a.salidas)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(e.code, file=sys.stderr)
            sys.exit(1)
