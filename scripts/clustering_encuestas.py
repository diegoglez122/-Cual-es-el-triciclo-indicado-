#!/usr/bin/env python3
"""Clustering de clientes (encuestas) para perfilar segmentos."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "processed" / "encuestas.json"
SALIDA_DIR = ROOT / "data" / "processed" / "clustering_encuestas"
SALIDA_CSV = SALIDA_DIR / "dw_clusters_encuestas.csv"

KS = (2, 3)


def normalizar_capacidad(v):
    if v is None:
        return np.nan
    s = str(v).strip().lower()
    if s in ("mas_5", "mas de 5", ">5", "mas de5"):
        return 1
    if s in ("hasta_5", "5 o menos", "<=5", "hasta 5"):
        return 0
    return np.nan


def tipo_mas_comun(sub):
    vals = sub["tipo_triciclo"].dropna()
    if vals.empty:
        return "desconocido"
    return vals.mode().iloc[0]


def etiqueta_negocio(presupuesto, tipo_pref, ingresos):
    tipo_pref_l = str(tipo_pref).lower()
    if "hibrid" in tipo_pref_l:
        return "Dueños de híbridos con perfil mixto"
    if tipo_pref_l == "electrico" or tipo_pref_l == "eléctrico":
        if pd.notna(presupuesto) and presupuesto >= 4000:
            return "Propietarios eléctricos con alto presupuesto"
        if pd.notna(ingresos) and ingresos >= 4000:
            return "Choferes de pasaje eléctrico con buenos ingresos"
        return "Choferes de pasaje con presupuesto ajustado"
    if "gas" in tipo_pref_l or "combust" in tipo_pref_l:
        return "Usuarios de triciclo a combustible / carga"
    if pd.notna(presupuesto) and presupuesto >= 4500:
        return "Dueños de carga con alto presupuesto"
    return "Segmento con presupuesto ajustado"


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"ERROR: no existe {JSON_PATH}")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(data)

    # Limpieza
    df["precio_vehiculo_usd"] = pd.to_numeric(df["precio_vehiculo_usd"], errors="coerce")
    df["ingreso_diario_cup"] = pd.to_numeric(df["ingreso_diario_cup"], errors="coerce")
    df["dias_semana"] = pd.to_numeric(df["dias_semana"], errors="coerce")
    df["capacidad_num"] = df["capacidad"].apply(normalizar_capacidad)
    df["tipo_triciclo"] = df["tipo_triciclo"].astype(str).str.lower().replace("nan", np.nan)
    df["tipo_triciclo"] = df["tipo_triciclo"].replace({"eléctrico": "electrico"})

    # Eliminar filas con valores críticos nulos
    df_clean = df.dropna(subset=["precio_vehiculo_usd", "ingreso_diario_cup", "capacidad_num"]).copy()
    if df_clean.empty:
        raise SystemExit("ERROR: sin datos válidos tras limpieza")

    # Features para clustering
    df_model = df_clean.copy()
    for col in ["precio_vehiculo_usd", "ingreso_diario_cup", "dias_semana", "capacidad_num"]:
        df_model[col] = df_model[col].fillna(df_model[col].median())

    dummies = pd.get_dummies(df_model["tipo_triciclo"], prefix="tipo")
    X = pd.concat(
        [df_model[["precio_vehiculo_usd", "capacidad_num", "ingreso_diario_cup", "dias_semana"]], dummies],
        axis=1,
    )
    Xs = StandardScaler().fit_transform(X)

    resultados_sil = []
    for k in KS:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Xs)
        if len(set(labels)) < 2:
            continue
        resultados_sil.append((k, silhouette_score(Xs, labels)))
    mejor_k, mejor_sil = max(resultados_sil, key=lambda t: t[1])
    etiquetas = KMeans(n_clusters=mejor_k, n_init=10, random_state=42).fit_predict(Xs)

    df_clean = df_clean.copy()
    df_clean["cluster"] = etiquetas

    print("=== CLUSTERING DE CLIENTES (ENCUESTAS) ===")
    print(f"Encuestados analizados: {len(df_clean)} / {len(df)} (tras limpieza)")
    print("\nSilhouette por k:")
    for k, s in resultados_sil:
        print(f"  k={k}: {s:.4f}")
    print(f"\nMejor k={mejor_k} (silhouette={mejor_sil:.4f})")

    perfiles = []
    for c in range(mejor_k):
        sub = df_clean[df_clean["cluster"] == c]
        presupuesto = sub["precio_vehiculo_usd"].mean()
        ingresos = sub["ingreso_diario_cup"].mean()
        tipo_pref = tipo_mas_comun(sub)
        etiqueta = etiqueta_negocio(presupuesto, tipo_pref, ingresos)
        print(f"\nClúster {c+1}: {etiqueta}")
        print(f"  Cantidad: {len(sub)}")
        print(f"  Presupuesto promedio USD: {presupuesto:.2f}")
        print(f"  Ingresos diarios promedio CUP: {ingresos:.2f}")
        print(f"  Tipo preferido: {tipo_pref}")
        print(f"  Modalidad más común: {sub['modalidad'].mode().iloc[0] if not sub['modalidad'].mode().empty else 'N/A'}")
        perfiles.append({
            "cluster_id": c + 1,
            "etiqueta_negocio": etiqueta,
            "cantidad_encuestados": int(len(sub)),
            "presupuesto_promedio_usd": round(float(presupuesto), 2),
            "tipo_preferido": tipo_pref,
        })

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(perfiles)[["cluster_id", "etiqueta_negocio", "cantidad_encuestados", "presupuesto_promedio_usd", "tipo_preferido"]].to_csv(
        SALIDA_CSV, index=False, encoding="utf-8"
    )
    print(f"\nCSV -> {SALIDA_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
