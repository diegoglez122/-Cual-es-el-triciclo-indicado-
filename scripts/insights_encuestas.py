#!/usr/bin/env python3
"""EDA avanzado de encuestas - listo para copiar al informe."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "processed" / "encuestas.json"
SALIDA_DIR = ROOT / "data" / "processed" / "encuestas_eda"
CATALOGOS_CSV = ROOT / "data" / "processed" / "catalogos" / "catalogo_consolidado.csv"
REVOLICO_JSON = ROOT / "data" / "processed" / "triciclos_aceptados_normalizado.json"


def norm_si_no(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    s = str(x).strip().lower()
    if s in ("si", "sí", "1", "true"):
        return "Si"
    if s in ("no", "0", "false"):
        return "No"
    return str(x).strip()


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"ERROR: no existe {JSON_PATH}")
    df = pd.DataFrame(json.loads(JSON_PATH.read_text(encoding="utf-8")))

    # Normalizaciones
    df["precio_vehiculo_usd"] = pd.to_numeric(df["precio_vehiculo_usd"], errors="coerce")
    df["ingreso_diario_cup"] = pd.to_numeric(df["ingreso_diario_cup"], errors="coerce")
    df["costo_luz_mes_cup"] = pd.to_numeric(df["costo_luz_mes_cup"], errors="coerce")
    df["es_duenio"] = df["es_duenio"].apply(norm_si_no)
    df["precio_pasaje_fijo"] = df["precio_pasaje_fijo"].apply(norm_si_no)
    df["usa_panel_solar"] = df["usa_panel_solar"].apply(norm_si_no)
    df["afectado_estatales"] = df["afectado_estatales"].apply(norm_si_no)
    df["piezas_bateria"] = df["piezas_bateria"].apply(norm_si_no)
    df["piezas_gomas"] = df["piezas_gomas"].apply(norm_si_no)
    df["piezas_motor"] = df["piezas_motor"].apply(norm_si_no)
    df["recupero_inversion"] = df["recupero_inversion"].apply(norm_si_no)

    for col in ["doc_licencia", "doc_circular", "doc_operativa", "doc_onat", "doc_otros"]:
        df[f"{col}_n"] = df[col].apply(lambda x: 1 if norm_si_no(x) == "Si" else 0)
    df["num_documentos"] = df[[c for c in df.columns if c.endswith("_n") and c != "doc_ninguno_n"]].sum(axis=1)

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("INSIGHTS DE ENCUESTAS - EDA AVANZADO")
    print("=" * 80)
    print(f"Total encuestados: {len(df)}\n")

    # BLOQUE A
    print("## BLOQUE A: COMPORTAMIENTO Y NEGOCIO\n")

    print("### 1) Ganancias vs. Tiempo en negocio")
    ct1 = pd.crosstab(df["tiempo_en_negocio"], df["tendencia_ganancias"], margins=True)
    print(ct1)
    print()

    print("### 2) Fijación de precios")
    print("precio_pasaje_fijo:")
    print(df["precio_pasaje_fijo"].value_counts(dropna=False))
    print("\nfijacion_precio:")
    print(df["fijacion_precio"].value_counts(dropna=False))
    print()

    print("### 3) Impacto Estatal (afectado_estatales = Si)")
    df_est = df[df["afectado_estatales"] == "Si"]
    print(f"n={len(df_est)}")
    print(df_est["tendencia_ganancias"].value_counts())
    if not df_est.empty:
        print("Predominante:", df_est["tendencia_ganancias"].mode().iloc[0])
    print()

    print("### 4) Dueño vs Chofer")
    print(df["es_duenio"].value_counts(dropna=False))
    print("\nIngreso diario promedio (CUP):")
    print(df.groupby("es_duenio")["ingreso_diario_cup"].mean().round(2))
    print()

    print("### 5) Costo de vida - demanda_costo_vida = Disminuido")
    df_dem = df[df["demanda_costo_vida"].astype(str).str.lower() == "disminuido"]
    print(f"n={len(df_dem)}")
    print(df_dem["tendencia_ganancias"].value_counts())
    print()

    print("### 6) Recuperación de inversión")
    print("Valores únicos recupero_inversion:", df["recupero_inversion"].unique())
    print("\nPor recupero_inversion:")
    print(df.groupby("recupero_inversion")[["marca", "modalidad"]].agg(
        marca_top=("marca", lambda x: x.value_counts().index[0] if len(x.value_counts()) else None),
        modalidad_top=("modalidad", lambda x: x.value_counts().index[0] if len(x.value_counts()) else None),
        n=("marca", "count"),
    ))
    print()

    print("### 7) Electricidad - costo luz y panel solar")
    luz = df["costo_luz_mes_cup"].dropna()
    print(f"Costo luz mes (CUP) - promedio (n={len(luz)}): {luz.mean():.2f}")
    print("\nIngreso diario promedio por uso de panel solar:")
    print(df.groupby("usa_panel_solar")["ingreso_diario_cup"].mean().round(2))
    print()

    # BLOQUE B
    print("=" * 80)
    print("## BLOQUE B: FALLAS Y CALIDAD\n")

    print("### 8) Documentación legal - número de documentos por encuestado")
    dist_docs = df["num_documentos"].value_counts().sort_index()
    print(dist_docs)
    dw_docs = dist_docs.reset_index()
    dw_docs.columns = ["num_documentos", "cantidad_encuestados"]
    dw_docs.to_csv(SALIDA_DIR / "dw_documentos.csv", index=False, encoding="utf-8")
    print("Guardado: dw_documentos.csv")
    print()

    print("### 9) Fallas de batería (piezas_bateria = Si)")
    df_bat = df[df["piezas_bateria"] == "Si"]
    print(f"n={len(df_bat)}")
    if not df_bat.empty:
        print(df_bat["modalidad"].value_counts())
    print()

    print("### 10) Fallas de gomas (piezas_gomas = Si)")
    df_gom = df[df["piezas_gomas"] == "Si"]
    print(f"n={len(df_gom)}")
    if not df_gom.empty:
        print(df_gom["modalidad"].value_counts())
    print()

    print("### 11) Ranking de fallas por marca")
    df_fallas = df.copy()
    df_fallas["falla_bateria"] = (df_fallas["piezas_bateria"] == "Si").astype(int)
    df_fallas["falla_gomas"] = (df_fallas["piezas_gomas"] == "Si").astype(int)
    df_fallas["falla_motor"] = (df_fallas["piezas_motor"] == "Si").astype(int)
    ranking = df_fallas.groupby("marca").agg(
        total_encuestados=("marca", "count"),
        fallas_bateria=("falla_bateria", "sum"),
        fallas_gomas=("falla_gomas", "sum"),
        fallas_motor=("falla_motor", "sum"),
        total_fallas=("falla_bateria", lambda x: x.sum() + df_fallas.loc[x.index, "falla_gomas"].sum() + df_fallas.loc[x.index, "falla_motor"].sum()),
    ).sort_values("total_fallas", ascending=False)
    print(ranking)
    ranking.to_csv(SALIDA_DIR / "dw_fallas_marcas.csv", encoding="utf-8")
    print("Guardado: dw_fallas_marcas.csv")
    print()

    # BLOQUE C
    print("=" * 80)
    print("## BLOQUE C: CRUCE MAESTRO (FORMAL vs INFORMAL vs REAL)\n")

    print("### 12) Comparación de precios")
    precio_encuestas = df["precio_vehiculo_usd"].mean()
    print(f"Precio promedio encuestados (precio_vehiculo_usd): {precio_encuestas:.2f} USD (n={df['precio_vehiculo_usd'].notna().sum()})")

    precios_import = {}
    if CATALOGOS_CSV.exists():
        cat = pd.read_csv(CATALOGOS_CSV)
        for imp in ["MZ Products", "Kikihabana", "Nihao53"]:
            if imp in cat["nombre_importadora"].values:
                precios_import[imp] = cat[cat["nombre_importadora"] == imp]["precio_usd"].mean()
        print("\nPromedio por importadora (catálogo consolidado):")
        for k, v in precios_import.items():
            print(f"  {k}: {v:.2f} USD")

    mediana_revolico = None
    if REVOLICO_JSON.exists():
        rev = json.loads(REVOLICO_JSON.read_text(encoding="utf-8"))
        precios_r = [r.get("precio_publicado") for r in rev if r.get("moneda_original") == "USD" and r.get("precio_publicado")]
        mediana_revolico = pd.Series(precios_r).median()
        print(f"\nMediana Revolico (USD): {mediana_revolico:.2f} USD (n={len(precios_r)})")

    print("\nCONCLUSIÓN:")
    refs = []
    if precios_import:
        refs.append(f"promedio formal ({', '.join(precios_import.keys())}) ~{np.mean(list(precios_import.values())):.0f} USD")
    if mediana_revolico:
        refs.append(f"mediana Revolico {mediana_revolico:.0f} USD")
    if precio_encuestas > (np.mean(list(precios_import.values())) if precios_import else precio_encuestas):
        print(f"Los encuestados pagaron EN PROMEDIO MÁS CARO ({precio_encuestas:.0f} USD) que el mercado formal/catalogado ({', '.join(f'{k} {v:.0f}' for k,v in precios_import.items())}). Esto sugiere compra en el mercado informal o con márgenes de reventa/importación.")
    else:
        print(f"Los encuestados pagaron cercanos o por debajo del mercado formal; hay coincidencia con el mercado observado.")

    print("\n" + "=" * 80)
    print("ÉXITO: CSV guardados en data/processed/encuestas_eda/")
    print("=" * 80)


if __name__ == "__main__":
    main()
