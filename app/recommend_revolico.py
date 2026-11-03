"""Búsqueda sobre los anuncios de Revolico (mercado informal)."""
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RUTA_ANUNCIOS = (
    Path(__file__).resolve().parent.parent
    / "data" / "processed" / "triciclos_aceptados_normalizado.json"
)

COLUMNAS = [
    "marca_detectada", "tipo_triciclo", "tipo_uso", "ubicacion", "municipio",
    "precio_publicado", "autonomia_km", "voltaje_bateria",
    "fecha_publicacion", "moneda_original", "enlace",
]


def _normalizar(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower().replace("_", " ")
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def cargar_anuncios():
    """Lee el JSON de anuncios aceptados y deja las columnas con el tipo correcto."""
    if not RUTA_ANUNCIOS.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {RUTA_ANUNCIOS}")
    with open(RUTA_ANUNCIOS, encoding="utf-8") as archivo:
        df = pd.DataFrame(json.load(archivo))

    # Si falta alguna columna (algunos anuncios no traen todos los campos), se crea vacía.
    df = df.reindex(columns=COLUMNAS)
    for columna in ("precio_publicado", "autonomia_km", "voltaje_bateria"):
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")

    # Protección: el presupuesto es en USD, así que no se mezclan otras monedas.
    en_usd = df["moneda_original"].astype(str).str.strip().str.upper().eq("USD")
    return df[en_usd | df["moneda_original"].isna()].reset_index(drop=True)


def recomendar_anuncios(df, presupuesto, uso, tipo, provincia, prioridad, n=5):
    """Devuelve (los n mejores anuncios, total que cumple los filtros)."""
    df = df.copy()

    if presupuesto is not None:
        df = df[df["precio_publicado"] <= presupuesto]

    uso_n = _normalizar(uso)
    if uso_n in ("carga", "pasajeros"):
        df = df[df["tipo_uso"].apply(_normalizar) == uso_n]

    tipo_n = _normalizar(tipo)
    if tipo_n not in ("", "me da igual", "cualquiera", "todos"):
        df = df[df["tipo_triciclo"].apply(_normalizar) == tipo_n]

    provincia_n = _normalizar(provincia)
    if provincia_n not in ("", "cualquiera", "todas"):
        df = df[df["ubicacion"].apply(_normalizar) == provincia_n]

    prioridad_n = _normalizar(prioridad)
    if prioridad_n == "autonomia":
        df = df.sort_values("autonomia_km", ascending=False, na_position="last")
    elif prioridad_n == "mas recientes":
        df = df.sort_values("fecha_publicacion", ascending=False, na_position="last")
    else:
        df = df.sort_values("precio_publicado", ascending=True, na_position="last")

    total = len(df)
    return df.head(n).reset_index(drop=True), total