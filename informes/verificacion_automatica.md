# Verificación automática e independiente de cifras del informe

Generada con `uv run scripts/verificar_cifras.py`. Cada cifra se recalcula sin el servidor MCP ni las Skills: el BCRP directo de su API y la ENAHO directo del archivo del INEI. Complementa la verificación manual de [`verificacion.md`](verificacion.md).

| Afirmación | Informe | Recalculado | Diferencia | ¿Coincide? | Cómo se recalculó |
|---|---:|---:|---:|:---:|---|
| Crédito directo en Piura a fin de 2024 (millones de S/) | 9 049.122 | 9 049.122 | -0.0001 | sí | API del BCRP, serie RD16184DA, año 2024 |
| Crédito directo total del Perú a fin de 2024 (millones de S/) | 407 351.740 | 407 351.742 | +0.0020 | sí | API del BCRP, serie RD16202DA (total), frente a la suma de los 25 |
| Inflación de Lima, dic-2020 a dic-2024 (%) | 21.514 | 21.514 | +0.0000 | sí | API del BCRP, índice PN38705PM de diciembre de cada año |
| Pobreza monetaria nacional 2024 (%) | 27.580 | 27.580 | +0.0000 | sí | sumaria-2024.dta del INEI leída directo, factor07 × mieperho |
| Pobreza monetaria en Piura 2024 (%) | 31.860 | 31.860 | +0.0000 | sí | la misma sumaria, ubigeo que empieza con 20 |
| Crédito por habitante en Piura 2024 (S/) | 4 550.600 | 4 550.600 | +0.0000 | sí | crédito de la API ÷ población de Piura de la sumaria |
| Spearman pobreza vs. crédito por habitante, 25 departamentos | -0.604 | -0.604 | +0.0000 | sí | Pearson de pandas sobre los rangos (la definición de Spearman), de salidas/cruce_credito_directo.csv |

Resultado: 7 de 7 cifras coinciden dentro de su tolerancia.
