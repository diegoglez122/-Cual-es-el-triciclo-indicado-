#!/usr/bin/env python3
"""Gráfico de adquisición del triciclo: importado vs comprado en Cuba.

Genera:
  - docs/graficos_eda/05_como_adquirio.png
  - data/processed/encuestas_eda/dw_como_adquirio.csv

Uso:
  python scripts/grafico_adquisicion.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
ENCUESTAS_JSON = ROOT / "data" / "processed" / "encuestas.json"
SALIDA_CSV = ROOT / "data" / "processed" / "encuestas_eda" / "dw_como_adquirio.csv"
SALIDA_PNG = ROOT / "docs" / "graficos_eda" / "05_como_adquirio.png"

ETIQUETAS = {
    "comprado_aqui": "Comprado aquí",
    "importado": "Importado",
}
ORDEN = ["Comprado aquí", "Importado"]


def cargar() -> pd.DataFrame:
    if not ENCUESTAS_JSON.exists():
        raise SystemExit(f"ERROR: no existe {ENCUESTAS_JSON}")
    return pd.DataFrame(json.loads(ENCUESTAS_JSON.read_text(encoding="utf-8")))


def resumen(df: pd.DataFrame) -> pd.DataFrame:
    conteo = df["como_adquirio"].replace(ETIQUETAS).value_counts().reindex(ORDEN, fill_value=0)
    resultado = conteo.rename_axis("como_adquirio").reset_index(name="cantidad")
    resultado["porcentaje"] = (resultado["cantidad"] / resultado["cantidad"].sum() * 100).round(1)
    return resultado


def grafico(datos: pd.DataFrame) -> None:
    SALIDA_PNG.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.barplot(
        data=datos,
        x="cantidad",
        y="como_adquirio",
        order=ORDEN,
        hue="como_adquirio",
        hue_order=ORDEN,
        palette="Set2",
        legend=False,
        ax=ax,
    )
    ax.set_title("¿Cómo adquirieron su triciclo los encuestados?")
    ax.set_xlabel("Cantidad de encuestados")
    ax.set_ylabel("")
    ax.set_xlim(0, datos["cantidad"].max() * 1.25)

    etiquetas = [
        f"{fila.cantidad} ({fila.porcentaje:.1f}%)"
        for fila in datos.itertuples(index=False)
    ]
    for contenedor, etiqueta in zip(ax.containers, etiquetas):
        ax.bar_label(contenedor, labels=[etiqueta], padding=5)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA_PNG, dpi=120, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    df = cargar()
    datos = resumen(df)
    SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(SALIDA_CSV, index=False, encoding="utf-8")
    grafico(datos)

    print("=== GRÁFICO DE ADQUISICIÓN COMPLETADO ===")
    print(f"CSV: {SALIDA_CSV.relative_to(ROOT)} ({SALIDA_CSV.stat().st_size} bytes)")
    print(f"PNG: {SALIDA_PNG.relative_to(ROOT)} ({SALIDA_PNG.stat().st_size} bytes)")
    print(datos.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
