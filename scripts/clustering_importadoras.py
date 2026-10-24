#!/usr/bin/env python3
"""Clustering de triciclos del mercado formal por características de producto.

Entrena KMeans (k=2 y k=3) sobre precio_usd, capacidad_carga_kg y el one-hot
de tipo. La importadora NO se usa como feature; solo se reporta en el perfil.

Uso:
  python scripts/clustering_importadoras.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("ERROR: falta scikit-learn. Instalar: pip install scikit-learn")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "data" / "processed" / "catalogos" / "catalogo_consolidado.csv"
SALIDA_DIR = ROOT / "data" / "processed" / "clustering_importadoras"
SALIDA_CSV = SALIDA_DIR / "dw_clusters_importadoras.csv"

VARIABLES_NUMERICAS = ["precio_usd", "capacidad_carga_kg"]
KS = (2, 3)


def cargar() -> pd.DataFrame:
    if not ENTRADA.exists():
        raise SystemExit(f"ERROR: no existe {ENTRADA}")
    df = pd.read_csv(ENTRADA)
    for col in VARIABLES_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def preparar_matriz(df: pd.DataFrame) -> np.ndarray:
    df_modelo = df.copy()
    for col in VARIABLES_NUMERICAS:
        df_modelo[col] = df_modelo[col].fillna(df_modelo[col].median())
    dummies = pd.get_dummies(df_modelo["tipo"], prefix="tipo")
    X = pd.concat([df_modelo[VARIABLES_NUMERICAS], dummies], axis=1)
    return StandardScaler().fit_transform(X)


def elegir_k(X: np.ndarray) -> tuple[int, list[tuple[int, float]], np.ndarray]:
    resultados = []
    for k in KS:
        etiquetas = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        score = silhouette_score(X, etiquetas)
        resultados.append((k, score))
    mejor_k, _ = max(resultados, key=lambda t: t[1])
    etiquetas_finales = KMeans(
        n_clusters=mejor_k, n_init=10, random_state=42
    ).fit_predict(X)
    return mejor_k, resultados, etiquetas_finales


def etiqueta_negocio(tipo: str, precio: float, capacidad: float,
                     precio_global: float, capacidad_mediana: float) -> str:
    if tipo == "combustion":
        if pd.notna(capacidad) and capacidad >= capacidad_mediana:
            return "Combustión premium de alta capacidad"
        return "Combustión de trabajo"
    if tipo == "electrico":
        if pd.notna(capacidad) and capacidad >= capacidad_mediana:
            return "Eléctricos de carga media"
        return "Eléctricos urbanos"
    if tipo == "hibrido":
        if pd.notna(precio) and precio < precio_global:
            return "Híbridos económicos"
        return "Híbridos premium"
    return f"Clúster {tipo}"


def perfilar(df: pd.DataFrame, etiquetas: np.ndarray) -> pd.DataFrame:
    precio_global = df["precio_usd"].mean()
    capacidad_mediana = df["capacidad_carga_kg"].median()
    perfiles = []

    for cluster in sorted(set(etiquetas)):
        sub = df[etiquetas == cluster]
        precio_prom = sub["precio_usd"].mean()
        capacidad_prom = sub["capacidad_carga_kg"].mean()
        tipo_top = sub["tipo"].mode().iloc[0] if not sub["tipo"].mode().empty else "desconocido"
        distribucion = sub["nombre_importadora"].value_counts()
        detalle_importadoras = ", ".join(
            f"{n} de {imp}" for imp, n in distribucion.items()
        )
        perfiles.append({
            "cluster_original": int(cluster),
            "etiqueta_negocio": etiqueta_negocio(
                tipo_top, precio_prom, capacidad_prom, precio_global, capacidad_mediana
            ),
            "cantidad_triciclos": len(sub),
            "precio_promedio_usd": round(float(precio_prom), 2),
            "capacidad_promedio_kg": round(float(capacidad_prom), 2),
            "tipo_dominante": tipo_top,
            "detalle_importadoras": detalle_importadoras,
        })

    perfil_df = pd.DataFrame(perfiles).sort_values(
        "precio_promedio_usd", ascending=False
    ).reset_index(drop=True)
    perfil_df["cluster_id"] = perfil_df.index + 1
    return perfil_df


def main() -> int:
    df = cargar()
    X = preparar_matriz(df)
    mejor_k, resultados, etiquetas = elegir_k(X)
    perfil = perfilar(df, etiquetas)

    print("=== CLUSTERING DE TRICICLOS (MARKET FORMAL) ===")
    print(f"Registros: {len(df)} | features: {VARIABLES_NUMERICAS} + one-hot(tipo)")
    print("\nSilhouette por k:")
    for k, score in resultados:
        print(f"  k={k}: {score:.4f}")
    print(f"\nMejor k={mejor_k} (silhouette={dict(resultados)[mejor_k]:.4f})")

    print("\nPerfil de clústeres:")
    for _, row in perfil.iterrows():
        print(
            f"  Clúster {row['cluster_id']}: {row['etiqueta_negocio']} | "
            f"n={row['cantidad_triciclos']} | "
            f"precio prom={row['precio_promedio_usd']:.2f} USD | "
            f"capacidad prom={row['capacidad_promedio_kg']:.2f} kg | "
            f"tipo top={row['tipo_dominante']}"
        )
        print(f"    importadoras: {row['detalle_importadoras']}")

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    columnas = [
        "cluster_id",
        "etiqueta_negocio",
        "cantidad_triciclos",
        "precio_promedio_usd",
        "capacidad_promedio_kg",
    ]
    perfil[columnas].to_csv(SALIDA_CSV, index=False, encoding="utf-8")
    print(f"\nCSV -> {SALIDA_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
