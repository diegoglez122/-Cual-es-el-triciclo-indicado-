"""Lógica de recomendación de triciclos para la aplicación web."""

from pathlib import Path
import unicodedata

import pandas as pd

# Ruta anclada a la raíz del proyecto para que funcione desde cualquier CWD.
RUTA_CATALOGO = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "catalogos"
    / "catalogo_consolidado.csv"
)

# Columnas exactas que consume la aplicación web.
COLUMNAS_SALIDA = [
    "marca",
    "modelo",
    "nombre_importadora",
    "precio_usd",
    "capacidad_carga_kg",
    "autonomia_km",
    "tipo",
    "tiene_panel_solar",
    "disponibilidad",
    "fecha_scraping",
    "url",
]


def _normalizar_texto(valor):
    """Minúsculas, sin tildes, sin guiones bajos y con espacios colapsados."""
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower().replace("_", " ")
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )
    return " ".join(texto.split())


def cargar_catalogo():
    """Lee el catálogo y fuerza la capacidad de carga a numérico."""
    if not RUTA_CATALOGO.exists():
        raise FileNotFoundError(f"No se encontró el catálogo: {RUTA_CATALOGO}")

    df = pd.read_csv(RUTA_CATALOGO)

    # Si aparecen textos como "Mas de 5", se convierten en nulos.
    df["capacidad_carga_kg"] = pd.to_numeric(
        df["capacidad_carga_kg"], errors="coerce"
    )
    df["precio_usd"] = pd.to_numeric(df["precio_usd"], errors="coerce")

    return df


def recomendar_triciclo(
    presupuesto,
    uso,
    tipo_preferido,
    prioridad,
    solo_en_stock,
    catalogo=None,
):
    """Devuelve el Top 3 de triciclos según los criterios del usuario.

    Parámetros:
        presupuesto: precio máximo en USD.
        uso: "Carga" o "Pasajeros".
        tipo_preferido: "Eléctrico", "Combustible", "Híbrido" o "Me da igual".
        prioridad: "Precio", "Autonomía" o "Capacidad".
        solo_en_stock: si es True, solo incluye unidades disponibles.
        catalogo: DataFrame opcional ya cargado. Si es None, se lee del CSV.

    Retorna un DataFrame con las columnas de COLUMNAS_SALIDA. Si no hay
    coincidencias, retorna un DataFrame vacío con esas mismas columnas.
    """
    df = (
        catalogo.copy() if catalogo is not None else cargar_catalogo().copy()
    )

    # Filtro por presupuesto. Los precios nulos quedan fuera al comparar.
    if presupuesto is not None:
        df = df[df["precio_usd"] <= presupuesto]

    # Filtro por uso: Carga exige 500 kg o más; Pasajeros, menos de 500 o sin dato.
    uso_normalizado = _normalizar_texto(uso)
    if uso_normalizado == "carga":
        df = df[df["capacidad_carga_kg"] >= 500]
    elif uso_normalizado == "pasajeros":
        df = df[
            df["capacidad_carga_kg"].isna()
            | (df["capacidad_carga_kg"] < 500)
        ]

    # Filtro por tipo, ignorando tildes y mayúsculas.
    tipo_normalizado = _normalizar_texto(tipo_preferido)
    if tipo_normalizado not in ("", "me da igual", "cualquiera", "todos"):
        tipos = df["tipo"].apply(_normalizar_texto)
        df = df[tipos == tipo_normalizado]

    # Filtro por stock, aceptando tanto "en stock" como "in_stock".
    if solo_en_stock:
        disponibilidad = df["disponibilidad"].apply(_normalizar_texto)
        df = df[disponibilidad.isin({"en stock", "in stock"})]

    # Orden según prioridad. Los nulos se mantienen al final.
    prioridad_normalizada = _normalizar_texto(prioridad)
    if prioridad_normalizada == "autonomia":
        df = df.sort_values(
            "autonomia_km", ascending=False, na_position="last"
        )
    elif prioridad_normalizada == "capacidad":
        df = df.sort_values(
            "capacidad_carga_kg", ascending=False, na_position="last"
        )
    else:
        # Fallback seguro: precio de menor a mayor.
        df = df.sort_values("precio_usd", ascending=True, na_position="last")

    # Top 3 con el esquema fijo, incluso cuando el resultado está vacío.
    return df.reindex(columns=COLUMNAS_SALIDA).head(3).reset_index(drop=True)
