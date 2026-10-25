#!/usr/bin/env python3
"""Exporta dos CSV adicionales para Datawrapper desde el EDA global.

Genera:
  - data/processed/dw_comparativa_precios.csv
  - data/processed/dw_vida_bateria_marcas.csv

Uso:
  python scripts/exportar_extra_dw.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CATALOGOS_CSV = ROOT / "data" / "processed" / "catalogos" / "catalogo_consolidado.csv"
ENCUESTAS_JSON = ROOT / "data" / "processed" / "encuestas.json"
REVOLICO_JSON = ROOT / "data" / "processed" / "triciclos_aceptados_normalizado.json"
SALIDA_COMPARATIVA = ROOT / "data" / "processed" / "dw_comparativa_precios.csv"
SALIDA_BATERIA = ROOT / "data" / "processed" / "dw_vida_bateria_marcas.csv"


def vida_bateria_meses(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    s = str(v).strip().lower()
    if s in ("", "nan", "none"):
        return np.nan
    mapeo = {
        "lt6m": 3,
        "6_12m": 9,
        "1_2a": 18,
        "2_3a": 30,
        "3_5a": 48,
        "gt5a": 66,
        "no_sabe": np.nan,
    }
    if s in mapeo:
        return mapeo[s]
    m_anios = re.findall(r"(\d+(?:\.\d+)?)\s*a[ñn]o", s)
    if m_anios:
        return float(m_anios[0]) * 12.0
    m_meses = re.findall(r"(\d+(?:\.\d+)?)\s*mes", s)
    if m_meses:
        return float(m_meses[0])
    return np.nan


def cargar_json(ruta: Path) -> list[dict]:
    if not ruta.exists():
        raise SystemExit(f"ERROR: no existe {ruta}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def construir_comparativa() -> pd.DataFrame:
    if not CATALOGOS_CSV.exists():
        raise SystemExit(f"ERROR: no existe {CATALOGOS_CSV}")

    catalogo = pd.read_csv(CATALOGOS_CSV)
    precios_formal = pd.to_numeric(catalogo["precio_usd"], errors="coerce").dropna()

    encuestas = pd.DataFrame(cargar_json(ENCUESTAS_JSON))
    precios_encuestados = pd.to_numeric(
        encuestas["precio_vehiculo_usd"], errors="coerce"
    ).dropna()

    revolico = cargar_json(REVOLICO_JSON)
    precios_informal = pd.Series(
        [
            float(r["precio_publicado"])
            for r in revolico
            if r.get("moneda_original") == "USD"
            and isinstance(r.get("precio_publicado"), (int, float))
        ],
        dtype="float64",
    )

    filas = []
    for segmento, precios in (
        ("Mercado Formal", precios_formal),
        ("Encuestados", precios_encuestados),
        ("Mercado Informal", precios_informal),
    ):
        filas.append(
            {
                "segmento": segmento,
                "precio_promedio_usd": round(float(precios.mean()), 2),
                "precio_mediana_usd": round(float(precios.median()), 2),
                "n": int(precios.size),
            }
        )
    return pd.DataFrame(filas)


def construir_bateria() -> pd.DataFrame:
    encuestas = pd.DataFrame(cargar_json(ENCUESTAS_JSON))
    encuestas["vida_bat_meses"] = encuestas["vida_bateria"].apply(vida_bateria_meses)

    resumen = (
        encuestas.groupby("marca")
        .agg(
            n=("marca", "size"),
            vida_bat_meses_prom=("vida_bat_meses", "mean"),
        )
        .dropna(subset=["vida_bat_meses_prom"])
        .sort_values("vida_bat_meses_prom", ascending=False)
        .reset_index()
    )
    resumen["vida_bat_meses_prom"] = resumen["vida_bat_meses_prom"].round(1)
    resumen["marca"] = resumen["marca"].replace({"Rali (dejar así)": "Rali"})
    return resumen[["marca", "n", "vida_bat_meses_prom"]]


def main() -> int:
    comparativa = construir_comparativa()
    bateria = construir_bateria()

    comparativa.to_csv(SALIDA_COMPARATIVA, index=False, encoding="utf-8")
    bateria.to_csv(SALIDA_BATERIA, index=False, encoding="utf-8")

    print("=== EXPORTACIÓN DATAWRAPPER COMPLETADA ===")
    print(f"Comparativa de precios: {len(comparativa)} filas")
    print(f"  {SALIDA_COMPARATIVA.relative_to(ROOT)} ({SALIDA_COMPARATIVA.stat().st_size} bytes)")
    print(f"Vida de batería por marca: {len(bateria)} filas")
    print(f"  {SALIDA_BATERIA.relative_to(ROOT)} ({SALIDA_BATERIA.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
