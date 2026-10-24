#!/usr/bin/env python3
"""EDA de los catálogos consolidados de triciclos.

Genera 4 gráficos PNG en docs/graficos_eda/ y 3 CSV agregados para Datawrapper
en data/processed/catalogos/.

Uso:
  python scripts/eda_catalogos.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "data" / "processed" / "catalogos" / "catalogo_consolidado.csv"
SALIDA_GRAFICOS = ROOT / "docs" / "graficos_eda"
SALIDA_DATOS = ROOT / "data" / "processed" / "catalogos"

TIPOS_ORDEN = ["electrico", "combustion", "hibrido"]
COLOR_PRINCIPAL = "#2b7bba"


def cargar() -> pd.DataFrame:
    if not ENTRADA.exists():
        raise SystemExit(f"ERROR: no existe {ENTRADA}")
    df = pd.read_csv(ENTRADA)
    for col in ("precio_usd", "capacidad_carga_kg", "autonomia_km"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def guardar_grafico(fig, nombre: str) -> Path:
    SALIDA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA_GRAFICOS / nombre
    fig.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return ruta


def tipos_presentes(df: pd.DataFrame) -> list[str]:
    presentes = set(df["tipo"].dropna().unique())
    orden = [t for t in TIPOS_ORDEN if t in presentes]
    return orden + sorted(presentes - set(orden))


def grafico_tipos(df: pd.DataFrame, orden: list[str]) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=df, x="tipo", order=orden, hue="tipo", hue_order=orden,
                  palette="Set2", legend=False, ax=ax)
    ax.set_title("Cantidad de triciclos por tipo")
    ax.set_xlabel("Tipo")
    ax.set_ylabel("Número de triciclos")
    for contenedor in ax.containers:
        ax.bar_label(contenedor)
    fig.tight_layout()
    return guardar_grafico(fig, "01_tipos.png")


def grafico_precios_importadora(df: pd.DataFrame) -> Path:
    datos = df.dropna(subset=["precio_usd", "nombre_importadora"])
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=datos, x="nombre_importadora", y="precio_usd",
                color=COLOR_PRINCIPAL, ax=ax)
    ax.set_title("Distribución de precios por importadora")
    ax.set_xlabel("Importadora")
    ax.set_ylabel("Precio (USD)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return guardar_grafico(fig, "02_precios_importadora.png")


def grafico_capacidad_vs_precio(df: pd.DataFrame, orden: list[str]) -> Path:
    datos = df.dropna(subset=["precio_usd", "capacidad_carga_kg"])
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=datos, x="capacidad_carga_kg", y="precio_usd",
                    hue="tipo", hue_order=orden, palette="Set2", s=90, ax=ax)
    ax.set_title("Capacidad de carga vs precio")
    ax.set_xlabel("Capacidad de carga (kg)")
    ax.set_ylabel("Precio (USD)")
    ax.legend(title="Tipo")
    fig.tight_layout()
    return guardar_grafico(fig, "03_capacidad_vs_precio.png")


def grafico_precio_promedio_tipo(df: pd.DataFrame, orden: list[str]) -> tuple[Path, pd.DataFrame]:
    resumen = (
        df.dropna(subset=["precio_usd"])
        .groupby("tipo", as_index=False)
        .agg(precio_promedio_usd=("precio_usd", "mean"), n_triciclos=("precio_usd", "size"))
    )
    resumen["precio_promedio_usd"] = resumen["precio_promedio_usd"].round(2)
    resumen["_orden"] = resumen["tipo"].apply(lambda t: orden.index(t) if t in orden else len(orden))
    resumen = resumen.sort_values("_orden").drop(columns="_orden").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=resumen, x="tipo", y="precio_promedio_usd", order=orden,
                hue="tipo", hue_order=orden, palette="Set2", legend=False, ax=ax)
    ax.set_title("Precio promedio por tipo de triciclo")
    ax.set_xlabel("Tipo")
    ax.set_ylabel("Precio promedio (USD)")
    for contenedor in ax.containers:
        ax.bar_label(contenedor, fmt="%.0f")
    fig.tight_layout()
    return guardar_grafico(fig, "04_precio_promedio_tipo.png"), resumen


def exportar_csv(df: pd.DataFrame, orden: list[str], resumen_tipo: pd.DataFrame) -> list[Path]:
    SALIDA_DATOS.mkdir(parents=True, exist_ok=True)
    rutas = []

    tipos = df["tipo"].value_counts().reindex(orden).dropna().astype(int)
    dw_tipos = tipos.rename_axis("tipo").reset_index(name="cantidad")
    dw_tipos["porcentaje"] = (dw_tipos["cantidad"] / dw_tipos["cantidad"].sum() * 100).round(2)
    ruta = SALIDA_DATOS / "dw_tipos.csv"
    dw_tipos.to_csv(ruta, index=False, encoding="utf-8")
    rutas.append(ruta)

    dw_importadora = (
        df.dropna(subset=["precio_usd"])
        .groupby("nombre_importadora", as_index=False)
        .agg(precio_promedio_usd=("precio_usd", "mean"), n_triciclos=("precio_usd", "size"))
    )
    dw_importadora["precio_promedio_usd"] = dw_importadora["precio_promedio_usd"].round(2)
    dw_importadora = dw_importadora.sort_values("precio_promedio_usd", ascending=False)
    ruta = SALIDA_DATOS / "dw_precios_importadora.csv"
    dw_importadora.to_csv(ruta, index=False, encoding="utf-8")
    rutas.append(ruta)

    ruta = SALIDA_DATOS / "dw_precio_tipo.csv"
    resumen_tipo[["tipo", "precio_promedio_usd", "n_triciclos"]].to_csv(
        ruta, index=False, encoding="utf-8"
    )
    rutas.append(ruta)

    return rutas


def main() -> int:
    sns.set_theme(style="whitegrid")
    df = cargar()
    orden = tipos_presentes(df)

    graficos = [
        grafico_tipos(df, orden),
        grafico_precios_importadora(df),
        grafico_capacidad_vs_precio(df, orden),
    ]
    ruta_prom, resumen_tipo = grafico_precio_promedio_tipo(df, orden)
    graficos.append(ruta_prom)

    csvs = exportar_csv(df, orden, resumen_tipo)

    print("=== EDA CATÁLOGOS COMPLETADO ===")
    print(f"Filas analizadas: {len(df)}")
    print("\nGráficos:")
    for ruta in graficos:
        print(f"  {ruta.relative_to(ROOT)} ({ruta.stat().st_size} bytes)")
    print("\nCSV para Datawrapper:")
    for ruta in csvs:
        print(f"  {ruta.relative_to(ROOT)} ({ruta.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
