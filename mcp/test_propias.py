"""Las 2 pruebas propias: revisan la herramienta panel_departamental contra cifras oficiales del BCRP.

    uv run pytest -q          # test_server.py (las 8 de la sesión, sin cambios) + estas 2 = 10 passed

Las cifras esperadas se tomaron directamente del BCRP, sin pasar por el servidor: crédito directo del sistema
financiero al sector privado, fin de año, millones de S/ (series anuales RD16184DA Piura, RD16169DA Lima y
RD16145DA Callao). Se pueden ver en
https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/RD16184DA/html/2020/2024/
"""
import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from server import mcp

PIURA_2020 = 8630.48299845
PIURA_2024 = 9049.12191293
LIMA_2024 = 298472.25519202
CALLAO_2024 = 6288.52842072


async def _con_cliente(f):
    async with Client(mcp) as c:
        return await f(c)


def llamar(herramienta, **args):
    return asyncio.run(_con_cliente(lambda c: c.call_tool(herramienta, args))).data


def test_panel_departamental_trae_los_25_departamentos_con_el_codigo_del_inei():
    r = llamar("panel_departamental", indicador="credito directo", anio=2024)
    deps = {d["ccdd"]: d for d in r["departamentos"]}
    assert sorted(deps) == [f"{i:02d}" for i in range(1, 26)]           # los mismos códigos que ubigeo[:2]
    assert deps["20"]["valor"] == pytest.approx(PIURA_2024, abs=0.01)
    assert deps["15"]["valor"] == pytest.approx(LIMA_2024, abs=0.01)     # Lima y Callao van separados
    assert deps["07"]["valor"] == pytest.approx(CALLAO_2024, abs=0.01)
    assert deps["15"]["puesto"] == 1 and r["faltantes"] == []
    assert r["fuente"].startswith("https://estadisticas.bcrp.gob.pe")


def test_panel_departamental_calcula_la_variacion_y_avisa_si_el_indicador_no_existe():
    r = llamar("panel_departamental", indicador="credito directo", anio=2024, anio_base=2020)
    piura = next(d for d in r["departamentos"] if d["ccdd"] == "20")
    assert piura["valor_base"] == pytest.approx(PIURA_2020, abs=0.01)
    assert piura["variacion_pct"] == pytest.approx((PIURA_2024 / PIURA_2020 - 1) * 100, abs=0.001)
    with pytest.raises(ToolError, match="cosecha de nubes"):
        llamar("panel_departamental", indicador="cosecha de nubes", anio=2024)
