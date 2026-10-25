#!/usr/bin/env python3
"""
Scraper de catálogos de Nihao53 (nihao53.com) — triciclos.

Sitio Odoo/ecommerce. Usa búsqueda interna por "triciclo" para descubrir
productos, y extrae ficha de cada producto.

Precios:
  - Se guarda el precio numérico publicado (list_price). Si no hay numérico
    visible o dice "Consultar", precio_usd queda None con precio_consultar=true.

Salidas:
  - Crudo:  scraping/data/catalogos/nihao53_raw.json
  - Limpio: data/processed/catalogos/nihao53_limpio.csv

Uso:
  source venv/bin/activate
  python scraping/catalogos/scraper_nihao53.py
  python scraping/catalogos/scraper_nihao53.py --solo <URL_DE_PRODUCTO>
  python scraping/catalogos/scraper_nihao53.py --paginas 5 --pausa 3
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlencode

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
SITIO = "https://nihao53.com"
NOMBRE_IMPORTADORA = "Nihao53"

DIR_CRUDO = RAIZ / "scraping" / "data" / "catalogos"
DIR_LIMPIO = RAIZ / "data" / "processed" / "catalogos"
ARCHIVO_CRUDO = DIR_CRUDO / "nihao53_raw.json"
ARCHIVO_CSV = DIR_LIMPIO / "nihao53_limpio.csv"

URL_BUSQUEDA_BASE = f"{SITIO}/shop"
TERMINO_BUSQUEDA = "triciclo"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/155.0.0.0 Safari/537.36"
)

TIMEOUT = 15
MAX_PAGINAS = 20

COLUMNAS_CSV = [
    "id",
    "nombre_importadora",
    "precio_usd",
    "marca",
    "modelo",
    "tipo",
    "tiene_panel_solar",
    "capacidad_carga_kg",
    "autonomia_km",
    "voltaje_bateria",
    "disponibilidad",
    "url",
    "fecha_scraping",
]

RE_TIPO_ELECTRICO = re.compile(r"electric|electron|bateria|lithium|litio", re.IGNORECASE)
RE_TIPO_COMBUSTION = re.compile(r"combustion|gasolina|gasoleo|fuel", re.IGNORECASE)
RE_TIPO_HIBRIDO = re.compile(r"hibrid", re.IGNORECASE)

RE_PANEL_SOLAR = re.compile(r"panel\s+solar|\bsolar\b|fotovoltaic[oa]?", re.IGNORECASE)

ETIQUETAS_AUTONOMIA = (
    "autonomia",
    "autonomía",
    "rango",
    "distancia",
)
ETIQUETAS_VOLTAJE = (
    "voltaje",
    "voltaje bateria",
    "voltaje de bateria",
    "bateria",
)
ETIQUETAS_CARGA = (
    "capacidad de carga",
    "carga",
    "capacidad",
)

RE_PRECIO_CONSULTAR = re.compile(
    r"\bconsult(?:ar|e|a|arlo|arla)?\b|a convenir|cotiza(?:r|ci[oó]n)?|precio a pedido",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------


def log(mensaje: str) -> None:
    print(f"[nihao53] {mensaje}", flush=True)


def crear_sesion() -> requests.Session:
    sesion = requests.Session()
    reintentos = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adaptador = HTTPAdapter(max_retries=reintentos)
    sesion.mount("https://", adaptador)
    sesion.mount("http://", adaptador)
    sesion.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "es-ES,es;q=0.9"})
    return sesion


def descargar(sesion: requests.Session, url: str, pausa: float) -> str | None:
    for intento in range(3):
        try:
            log(f"GET {url} (intento {intento + 1}/3)")
            respuesta = sesion.get(url, timeout=TIMEOUT)
            if respuesta.status_code == 200:
                return respuesta.text
            log(f"HTTP {respuesta.status_code} en {url}")
            if respuesta.status_code in (401, 403, 404, 410):
                return None
        except requests.RequestException as exc:
            log(f"error de red en {url}: {exc}")
        if intento < 2:
            time.sleep(pausa * (intento + 2))
    return None


def normalizar_espacios(texto: str | None) -> str:
    return re.sub(r"\s+", " ", (texto or "")).strip()


def sin_acentos(texto: str | None) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower().strip()


def a_numero(texto: str | None) -> float | None:
    if not texto:
        return None
    limpio = re.sub(r"[^\d.,-]", "", texto)
    if not limpio or not re.search(r"\d", limpio):
        return None
    # Formato europeo: miles con punto, decimales con coma (ej. 3.330,00)
    if "," in limpio and "." in limpio:
        # quitar puntos (miles), convertir coma a punto
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        partes = limpio.split(",")
        if len(partes) == 2 and len(partes[-1]) <= 2:
            limpio = limpio.replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "." in limpio:
        partes = limpio.split(".")
        if len(partes) == 2 and len(partes[-1]) <= 2:
            pass  # decimal
        elif len(partes) >= 2:
            # miles
            limpio = limpio.replace(".", "")
    try:
        return float(limpio)
    except ValueError:
        return None


def inferir_tipo(url: str | None, titulo: str | None) -> str:
    """Infiere el tipo usando solo URL y título, con prioridad a híbrido/combustión."""
    texto = sin_acentos(f"{url or ''} {titulo or ''}")
    if RE_TIPO_HIBRIDO.search(texto):
        return "híbrido"
    if RE_TIPO_COMBUSTION.search(texto):
        return "combustión"
    if RE_TIPO_ELECTRICO.search(texto):
        return "eléctrico"
    return "desconocido"


def a_rango_numerico(texto: str | None) -> str:
    if not texto:
        return ""
    numeros = re.findall(r"\d+(?:[.,]\d+)?", texto)
    if not numeros:
        return ""
    if len(numeros) >= 2:
        return f"{numeros[0]}-{numeros[-1]}"
    return numeros[0]


# ---------------------------------------------------------------------------
# Descubrimiento de URLs
# ---------------------------------------------------------------------------


def descubrir_urls(sesion: requests.Session, pausa: float, max_paginas: int) -> tuple[list[str], list[str]]:
    visitadas: list[str] = []
    urls_encontradas: set[str] = set()

    for pagina in range(1, max_paginas + 1):
        params = {"search": TERMINO_BUSQUEDA}
        if pagina > 1:
            params["page"] = pagina
        url = f"{URL_BUSQUEDA_BASE}?{urlencode(params)}"
        visitadas.append(url)
        html = descargar(sesion, url, pausa)
        if not html:
            break
        soup = BeautifulSoup(html, "html.parser")

        for enlace in soup.find_all("a", href=True):
            href = enlace["href"]
            if "/shop/" not in href:
                continue
            if "/shop/category/" in href:
                continue
            if href.endswith("/shop"):
                continue
            if re.search(r"/shop/[a-z0-9\-]+-\d+", href):
                url_prod = urljoin(SITIO, href.split("?")[0])
                href_low = url_prod.lower()
                if "cuatri" in href_low or "cuatro" in href_low or "4-plaza" in href_low or "4rueda" in href_low:
                    continue
                if any(x in href_low for x in ["goma", "neumatico", "repuesto", "bateria", "motor"]):
                    continue
                urls_encontradas.add(url_prod)

        time.sleep(pausa)
        if len(urls_encontradas) == 0 and pagina == 1:
            break

    return sorted(list(urls_encontradas)), visitadas


# ---------------------------------------------------------------------------
# Extracción de ficha
# ---------------------------------------------------------------------------


def extraer_ficha(sesion: requests.Session, url: str, pausa: float) -> dict[str, Any]:
    html = descargar(sesion, url, pausa)
    if not html:
        raise RuntimeError(f"No se pudo descargar {url}")
    soup = BeautifulSoup(html, "html.parser")

    titulo = ""
    h1 = soup.find("h1")
    if h1:
        titulo = normalizar_espacios(h1.get_text())

    # Precio
    precio_usd = None
    precio_consultar = False
    texto_precio = ""
    # Buscar en elementos con clase precio
    for sel in soup.select(".oe_price, .product_price, .price, .oe_currency_value, [itemprop='price']"):
        t = normalizar_espacios(sel.get_text())
        if t and "$" in t or re.search(r"\d", t):
            texto_precio = t
            break
    if not texto_precio:
        # buscar texto con $ numérico
        m = re.search(r"\$\s*([\d][\d.,]+)", html)
        if m:
            texto_precio = "$ " + m.group(1)
        else:
            m2 = re.search(r"([\d][\d.,]+)\s*USD", html, re.I)
            if m2:
                texto_precio = "$ " + m2.group(1)

    if texto_precio and RE_PRECIO_CONSULTAR.search(texto_precio):
        precio_consultar = True
        precio_usd = None
        log(f"precio: CONSULTAR en {url}")
    elif texto_precio:
        precio_usd = a_numero(texto_precio)
        if precio_usd is None or precio_usd == 0.0:
            # intentar extraer solo el primer número
            m = re.search(r"([\d][\d.,]+)", texto_precio)
            if m:
                precio_usd = a_numero(m.group(1))
        if precio_usd is None:
            log(f"precio: NO NUMÉRICO en {url} -> texto='{texto_precio}'")
            precio_usd = None
        elif precio_usd == 0.0:
            log(f"precio: 0.0 en {url} -> texto='{texto_precio}' (se guarda como null)")
            precio_usd = None

    # SKU/ID
    sku = ""
    m = re.search(r"product\.template[\/\s]+(\d+)", html)
    if m:
        sku = m.group(1)
    id_post = sku or url.split("-")[-1].split("?")[0]

    # Descripción
    desc = ""
    for sel in soup.select("#product_details, .oe_structure, .product-description, .description"):
        desc = normalizar_espacios(sel.get_text())
        if len(desc) > 50:
            break

    texto_tecnico = f"{titulo} {desc}"

    # Tipo (solo URL + título: la descripción suele mencionar componentes eléctricos
    # aunque el triciclo sea de combustión)
    tipo = inferir_tipo(url, titulo)

    # Panel solar
    tiene_panel_solar = bool(RE_PANEL_SOLAR.search(texto_tecnico))

    # Especificaciones
    autonomia = ""
    voltaje = ""
    capacidad_carga = ""
    for tabla in soup.find_all("table"):
        for fila in tabla.find_all("tr"):
            celdas = fila.find_all(["td", "th"])
            if len(celdas) >= 2:
                etiqueta = sin_acentos(celdas[0].get_text())
                valor = normalizar_espacios(celdas[1].get_text())
                if any(k in etiqueta for k in ETIQUETAS_AUTONOMIA):
                    autonomia = a_rango_numerico(valor) or a_rango_numerico(texto_tecnico)
                if any(k in etiqueta for k in ETIQUETAS_VOLTAJE):
                    voltaje = a_rango_numerico(valor)
                    m = re.findall(r"\d{2,3}", voltaje)
                    if m:
                        voltaje = m[0]
                if any(k in etiqueta for k in ETIQUETAS_CARGA):
                    capacidad_carga = a_rango_numerico(valor)

    if not autonomia:
        m = re.search(r"autonom[íi]a[^0-9]{0,20}(\d+[-–]\d+|\d+)\s*km", texto_tecnico, re.I)
        if m:
            autonomia = a_rango_numerico(m.group(0))
    if not voltaje:
        m = re.search(r"(\d{2,3})\s*v\b", texto_tecnico, re.I)
        if m:
            voltaje = m.group(1)
    if not capacidad_carga:
        m = re.search(r"carga[^0-9]{0,15}(\d+)\s*kg", texto_tecnico, re.I)
        if m:
            capacidad_carga = m.group(1)

    # Disponibilidad
    disponibilidad = "desconocido"
    if re.search(r"en\s+stock|disponible", texto_tecnico, re.I):
        disponibilidad = "en_stock"
    elif re.search(r"agotad|sin\s+existencia|no\s+disponible", texto_tecnico, re.I):
        disponibilidad = "agotado"

    # Marca/modelo
    marca = "Desconocida"
    # Intentar extraer de título
    palabras = titulo.split()
    if palabras:
        marca_cand = palabras[0]
        if marca_cand.lower() not in ("triciclo", "cuatriciclo", "goma"):
            marca = marca_cand
    # Buscar en descripción si sigue desconocida
    if marca == "Desconocida" and desc:
        m = re.search(r"\bmarca\s*:?\s*([A-Z][A-Za-z0-9\-]+)", desc, re.I)
        if not m:
            m = re.search(r"\b([A-Z][A-Za-z]{2,10})\b", desc)
        if m:
            cand = m.group(1)
            if cand.lower() not in ("triciclo", "cuatriciclo", "electrico", "combustion", "pasajeros", "carga"):
                marca = cand
    # Si sigue vacía/desconocida, usar Nihao53
    if not marca or marca == "Desconocida" or marca.strip() == "":
        marca = "Nihao53"

    modelo = titulo
    if marca and marca != "Nihao53" and modelo.lower().startswith(marca.lower()):
        modelo = modelo[len(marca):].strip()
    elif marca == "Nihao53":
        modelo = titulo

    return {
        "id": id_post,
        "url": url,
        "titulo": titulo,
        "sku": sku,
        "nombre_importadora": NOMBRE_IMPORTADORA,
        "marca": marca,
        "modelo": modelo,
        "tipo": tipo,
        "precio_usd": precio_usd,
        "moneda": "USD",
        "texto_precio": texto_precio,
        "precio_en_oferta": False,
        "precio_consultar": precio_consultar,
        "tiene_panel_solar": tiene_panel_solar,
        "capacidad_carga_kg": capacidad_carga,
        "autonomia_km": autonomia,
        "voltaje_bateria": voltaje,
        "disponibilidad": disponibilidad,
        "categorias": ["triciclo"],
        "descripcion_corta": desc[:500] if desc else "",
        "fecha_scraping": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------


def fila_csv(ficha: dict[str, Any]) -> dict[str, Any]:
    precio = ficha.get("precio_usd")
    return {
        "id": ficha.get("id", ""),
        "nombre_importadora": ficha.get("nombre_importadora", ""),
        "precio_usd": "" if precio is None else f"{precio:.2f}",
        "marca": ficha.get("marca", ""),
        "modelo": ficha.get("modelo", ""),
        "tipo": ficha.get("tipo", ""),
        "tiene_panel_solar": "true" if ficha.get("tiene_panel_solar") else "false",
        "capacidad_carga_kg": ficha.get("capacidad_carga_kg", ""),
        "autonomia_km": ficha.get("autonomia_km", ""),
        "voltaje_bateria": ficha.get("voltaje_bateria", ""),
        "disponibilidad": ficha.get("disponibilidad", ""),
        "url": ficha.get("url", ""),
        "fecha_scraping": ficha.get("fecha_scraping", ""),
    }


def escribir_crudo(fichas: list[dict[str, Any]], visitadas: list[str], errores: list[dict[str, str]]) -> None:
    DIR_CRUDO.mkdir(parents=True, exist_ok=True)
    contenido = {
        "meta": {
            "institucion": NOMBRE_IMPORTADORA,
            "sitio": SITIO,
            "script": "scraping/catalogos/scraper_nihao53.py",
            "fecha_scraping": date.today().isoformat(),
            "urls_visitadas": visitadas,
            "n_urls_visitadas": len(visitadas),
            "n_productos": len(fichas),
            "n_errores": len(errores),
            "errores": errores,
        },
        "productos": fichas,
    }
    ARCHIVO_CRUDO.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"crudo -> {ARCHIVO_CRUDO.relative_to(RAIZ)} ({len(fichas)} productos)")


def escribir_csv(fichas: list[dict[str, Any]]) -> None:
    DIR_LIMPIO.mkdir(parents=True, exist_ok=True)
    with ARCHIVO_CSV.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_CSV)
        escritor.writeheader()
        for ficha in fichas:
            escritor.writerow(fila_csv(ficha))
    log(f"limpio -> {ARCHIVO_CSV.relative_to(RAIZ)} ({len(fichas)} filas)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    global TIMEOUT

    analizador = argparse.ArgumentParser(description="Scraper de triciclos en Nihao53")
    analizador.add_argument("--solo", metavar="URL", help="extrae una única ficha de producto")
    analizador.add_argument("--paginas", type=int, default=5, help="páginas de búsqueda a recorrer")
    analizador.add_argument("--pausa", type=float, default=3.0, help="pausa entre peticiones (s)")
    analizador.add_argument("--timeout", type=int, default=TIMEOUT, help="timeout HTTP (s)")
    argumentos = analizador.parse_args()

    TIMEOUT = argumentos.timeout
    if argumentos.paginas > MAX_PAGINAS:
        log(f"límite de seguridad: {argumentos.paginas} páginas -> {MAX_PAGINAS}")
        argumentos.paginas = MAX_PAGINAS

    log("Iniciando sesión HTTP...")
    sesion = crear_sesion()

    visitadas: list[str] = []
    errores: list[dict[str, str]] = []
    fichas: list[dict[str, Any]] = []

    if argumentos.solo:
        url = argumentos.solo
        if not urlparse(url).netloc:
            url = urljoin(SITIO, url)
        visitadas.append(url)
        log(f"modo --solo: {url}")
        try:
            fichas.append(extraer_ficha(sesion, url, argumentos.pausa))
        except Exception as exc:
            log(f"ERROR en {url}: {exc}")
            errores.append({"url": url, "error": str(exc)})
    else:
        log("Buscando productos con 'triciclo'...")
        urls, visitadas = descubrir_urls(sesion, argumentos.pausa, argumentos.paginas)
        log(f"{len(urls)} triciclos detectados")
    for indice, url in enumerate(urls, start=1):
        log(f"Extrayendo producto [{indice}/{len(urls)}]: {url}")
        try:
            ficha = extraer_ficha(sesion, url, argumentos.pausa)
            titulo_f = (ficha.get('titulo') or '').lower()
            if any(k in titulo_f for k in ['cuatriciclo', 'cuatro plazas', '4 ruedas']):
                log(f"EXCLUIDO (cuatriciclo): {url}")
                continue
            if any(k in titulo_f for k in ['goma', 'neumático', 'neumatico', 'repuesto', 'batería', 'bateria', 'motor']):
                log(f"EXCLUIDO (accesorio): {url}")
                continue
            # Solo aceptar si parece triciclo
            if not ('triciclo' in titulo_f or 'triciclo' in url.lower()):
                log(f"EXCLUIDO (no es triciclo): {url}")
                continue
            fichas.append(ficha)
            log(
                f"[{indice}/{len(urls)}] {ficha['modelo'] or ficha['titulo']} | "
                f"{ficha['precio_usd']} USD | marca={ficha['marca']} | {ficha['disponibilidad']}"
            )
        except Exception as exc:
            log(f"ERROR en {url}: {exc}")
            errores.append({"url": url, "error": str(exc)})
        time.sleep(argumentos.pausa)

    log("Escribiendo archivos de salida...")
    escribir_crudo(fichas, visitadas, errores)
    escribir_csv(fichas)

    log(f"fin: {len(fichas)} fichas, {len(errores)} errores")
    return 1 if errores and not fichas else 0


if __name__ == "__main__":
    sys.exit(main())
