#!/usr/bin/env python3
"""
Consolida los catálogos limpios de las importadoras.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIR_LIMPIO = RAIZ / "data" / "processed" / "catalogos"
ARCHIVOS = [
    DIR_LIMPIO / "mzproducts_limpio.csv",
    DIR_LIMPIO / "kikihabana_limpio.csv",
    DIR_LIMPIO / "nihao53_limpio.csv",
]
SALIDA = DIR_LIMPIO / "catalogo_consolidado.csv"


def main() -> int:
    dfs = []
    for archivo in ARCHIVOS:
        if archivo.exists():
            df = pd.read_csv(archivo)
            print(f"[consolidar] cargado {archivo.name}: {len(df)} filas")
            dfs.append(df)
        else:
            print(f"[consolidar] NO EXISTE {archivo}")

    if not dfs:
        print("[consolidar] No hay archivos para consolidar")
        return 1

    df = pd.concat(dfs, ignore_index=True)
    print(f"[consolidar] concatenado: {len(df)} filas")

    # Numéricos
    for col in ["precio_usd", "capacidad_carga_kg", "autonomia_km"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rellenos
    if "marca" in df.columns:
        df["marca"] = df["marca"].fillna("Desconocida")
    if "tipo" in df.columns:
        df["tipo"] = df["tipo"].fillna("No especificado")

    # Normalización de tipo
    def _sin_tildes(s):
        import unicodedata
        if pd.isna(s):
            return s
        s2 = unicodedata.normalize("NFKD", str(s))
        return "".join(c for c in s2 if not unicodedata.combining(c)).lower().strip()

    if "tipo" in df.columns:
        df["tipo_norm"] = df["tipo"].apply(_sin_tildes)
        def norm_tipo(x):
            if pd.isna(x):
                return "no_especificado"
            if x in ("electrico", "electric", "eletrico"):
                return "electrico"
            if x in ("combustion", "gasolina", "diesel", "combustible"):
                return "combustion"
            if x in ("hibrido", "hybrid"):
                return "hibrido"
            if x == "no especificado":
                return "no_especificado"
            return x
        df["tipo"] = df["tipo_norm"].apply(norm_tipo)
        df.drop(columns=["tipo_norm"], inplace=True)

    # Inferir tipo para Nihao53 desde raw si no especificado
    if "tipo" in df.columns and "nombre_importadora" in df.columns:
        import json
        raw_nihao = RAIZ / "scraping" / "data" / "catalogos" / "nihao53_raw.json"
        mapa_nihao = {}
        if raw_nihao.exists():
            try:
                data = json.loads(raw_nihao.read_text(encoding="utf-8"))
                for p in data.get("productos", []):
                    url_p = p.get("url") or ""
                    texto_p = " ".join([
                        str(p.get("titulo", "")),
                        str(p.get("modelo", "")),
                        url_p,
                        str(p.get("descripcion_corta", "")),
                        str(p.get("descripcion", "")),
                    ])
                    mapa_nihao[url_p] = _sin_tildes(texto_p)
                    if p.get("id"):
                        mapa_nihao[str(p.get("id"))] = _sin_tildes(texto_p)
            except Exception as e:
                print(f"[consolidar] aviso: no se pudo leer nihao53_raw.json: {e}")

        def inferir_tipo(row):
            if row.get("tipo") != "no_especificado":
                return row.get("tipo")
            if row.get("nombre_importadora") != "Nihao53":
                return row.get("tipo")
            texto = ""
            url_r = str(row.get("url", ""))
            if url_r in mapa_nihao:
                texto = mapa_nihao[url_r]
            else:
                texto = " ".join([
                    str(row.get("titulo", "")),
                    str(row.get("modelo", "")),
                    url_r,
                    str(row.get("descripcion_corta", "")),
                ])
                texto = _sin_tildes(texto)
            if any(k in texto for k in ["electrico", "electric", "bateria", "lithium", "litio"]):
                return "electrico"
            if any(k in texto for k in ["gasolina", "combustion", "fuel"]):
                return "combustion"
            if "hibrido" in texto:
                return "hibrido"
            return row.get("tipo")

        mask = df["nombre_importadora"] == "Nihao53"
        if mask.any():
            df.loc[mask, "tipo"] = df[mask].apply(inferir_tipo, axis=1)

    # Normalización de disponibilidad
    if "disponibilidad" in df.columns:
        df["disp_norm"] = df["disponibilidad"].apply(_sin_tildes)
        def norm_disp(x):
            if pd.isna(x):
                return "desconocido"
            if "stock" in x or "disponible" in x:
                return "en stock"
            if "agotad" in x or "sin" in x:
                return "agotado"
            return x
        df["disponibilidad"] = df["disp_norm"].apply(norm_disp)
        df.drop(columns=["disp_norm"], inplace=True)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"[consolidar] guardado -> {SALIDA.relative_to(RAIZ)}")

    print("\n=== RESUMEN ===")
    print(f"Total filas: {len(df)}")
    if "precio_usd" in df.columns:
        precios = df["precio_usd"].dropna()
        if len(precios) > 0:
            print(f"Precio promedio: {precios.mean():.2f} USD")
            print(f"Precio mediana: {precios.median():.2f} USD")
            print(f"Precio std: {precios.std():.2f} USD")
        else:
            print("Sin precios numéricos válidos")
    if "nombre_importadora" in df.columns:
        print("\n--- Por importadora ---")
        print(df["nombre_importadora"].value_counts())
    if "tipo" in df.columns:
        print("\n--- Por tipo ---")
        print(df["tipo"].value_counts())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
