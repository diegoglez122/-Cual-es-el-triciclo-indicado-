#!/usr/bin/env python3
"""
Scraper de catálogos de MZ Products (mzproducts.com) — triciclos.

Sitio WooCommerce. Descubre los productos de triciclo recorriendo la categoría
"Triciclos" y la búsqueda interna del sitio, y extrae las ficha de cada producto.

Salidas:
  - Crudo:  scraping/data/catalogos/mzproducts_raw.json
  - Limpio: data/processed/catalogos/mzproducts_limpio.csv

Uso:
  source venv/bin/activate
  python scraping/catalogos/scraper_mzproducts.py
  python scraping/catalogos/scraper_mzproducts.py --solo <URL_DE_PRODUCTO>
  python scraping/catalogos/scraper_mzproducts.py --paginas 3 --pausa 4

Reglas del proyecto aplicadas:
  - Nunca se inventan datos: si un campo no aparece en la ficha queda vacío ("").
  - Pausa >= 3 s entre peticiones HTTP.
  - Los crudos no se versionan (lo cubre .gitignore).
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
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]
SITIO = "https://www.mzproducts.com"
NOMBRE_IMPORTADORA = "MZ Products"

DIR_CRUDO = RAIZ / "scraping" / "data" / "catalogos"
DIR_LIMPIO = RAIZ / "data" / "processed" / "catalogos"
ARCHIVO_CRUDO = DIR_CRUDO / "mzproducts_raw.json"
ARCHIVO_CSV = DIR_LIMPIO / "mzproducts_limpio.csv"

# Candidatas de categoría: se prueban en orden hasta que una devuelva productos.
URLS_CATEGORIA = [
    f"{SITIO}/categoria-producto/transporte/triciclos-transporte/",
    f"{SITIO}/categoria-producto/transporte/triciclos/",
    f"{SITIO}/categoria-producto/triciclos/",
]

# Búsqueda interna de WordPress (post_type=product) — cubre productos con
# "triciclo" en el título que estén fuera de la categoría.
URL_BUSQUEDA = f"{SITIO}/?s=triciclo&post_type=product"

TERMINO_BUSQUEDA = "triciclo"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/155.0.0.0 Safari/537.36"
)

TIMEOUT = 60

# Cabecera del CSV limpio, en el orden definido para esta línea de scraping.
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

# Palabras que describen el tipo de propulsión (para el campo `tipo`).
RE_TIPO_ELECTRICO = re.compile(r"el[ée]ctric|electr[oó]nic", re.IGNORECASE)
RE_TIPO_COMBUSTION = re.compile(r"combusti[oó]n|combustion|gasolina|gas[oó]leo", re.IGNORECASE)

# Evidencia de panel solar. Exige "panel solar" o "solar"/"fotovoltaico" como
# palabra propia: así "Panel de instrumentos digital" NO se confunde.
RE_PANEL_SOLAR = re.compile(r"panel\s+solar|\bsolar\b|fotovoltaic[oa]?", re.IGNORECASE)

# Tokens técnicos que no forman parte del modelo comercial.
RE_TOKEN_TECNICO = re.compile(
    r"\d+\s*(?:v\b|volt|ah\b|amh|cc\b|w\b|watts?|kw\b|kg\b|kgs\b|lt|l\b|anos?|years?)",
    re.IGNORECASE,
)
RE_TOKEN_TECNICO_COMPUESTO = re.compile(r"\d+\s*[/x]\s*\d+\s*(?:ah|v)?", re.IGNORECASE)

# Etiquetas de especificación que alimentan cada campo del CSV.
ETIQUETAS_AUTONOMIA = (
    "autonomia por carga completa",
    "autonomia",
    "autonomia de la bateria",
)
ETIQUETAS_VOLTAJE = (
    "capacidad de la bateria",
    "voltaje de bateria",
    "voltaje",
)
ETIQUETAS_CARGA = (
    "capacidad de carga util",
    "capacidad de carga maxima",
    "capacidad de carga",
    "carga util",
)
ETIQUETAS_TIPO = ("tipo de conduccion", "tipo de propulsion", "tipo")


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------


def log(mensaje: str) -> None:
    print(f"[mzproducts] {mensaje}", flush=True)


def crear_sesion() -> requests.Session:
    """Sesión HTTP con reintentos ante 429/5xx."""
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
    """Descarga una URL. Devuelve el HTML o None si falló."""
    for intento in range(3):
        try:
            respuesta = sesion.get(url, timeout=TIMEOUT)
            if respuesta.status_code == 200:
                return respuesta.text
            log(f"HTTP {respuesta.status_code} en {url}")
            # 404/403/401 no mejoran reintentando: son definitivos.
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
    """Normaliza para comparar etiquetas ('Autonomía' == 'autonomia')."""
    descompuesto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower().strip()


def a_numero(texto: str | None) -> float | None:
    """Primer número de un texto ('4,680.00 USD' -> 4680.0)."""
    if not texto:
        return None
    limpio = re.sub(r"[^\d.,-]", "", texto)
    if not limpio or not re.search(r"\d", limpio):
        return None
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(",", "")
    elif "," in limpio:
        partes = limpio.split(",")
        limpio = partes[0] if len(partes[-1]) == 3 else limpio.replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        return None


def a_rango_numerico(texto: str | None) -> str:
    """
    Normaliza un valor con unidades a su contenido numérico.
      '120-180 km*' -> '120-180' | '100 a 120 km' -> '100-120' | '525 kg' -> '525'
    Devuelve '' si no hay números.
    """
    if not texto:
        return ""
    numeros = re.findall(r"\d+(?:[.,]\d+)?", texto)
    if not numeros:
        return ""
    # '1.4 x 2m' no es un rango de carga: se queda con el primer número.
    if len(numeros) == 2 and re.search(r"\bx\b", texto, re.IGNORECASE):
        return numeros[0]
    valores = []
    for numero in numeros:
        valor = a_numero(numero)
        if valor is None:
            continue
        valores.append(str(int(valor)) if float(valor).is_integer() else str(valor))
    return "-".join(valores)


# ---------------------------------------------------------------------------
# Descubrimiento de productos
# ---------------------------------------------------------------------------


def enlaces_producto(soup: BeautifulSoup, base: str) -> list[tuple[str, str]]:
    """Enlaces únicos a fichas de producto de la página: (url, texto_del_enlace)."""
    vistos: dict[str, str] = {}
    for enlace in soup.select("a[href]"):
        href = enlace.get("href") or ""
        if "/producto/" not in href:
            continue
        absoluta = urljoin(base, href.split("?")[0].split("#")[0])
        if absoluta not in vistos:
            vistos[absoluta] = normalizar_espacios(enlace.get_text(" ", strip=True))
    return list(vistos.items())


def es_triciclo(url: str, texto: str = "") -> bool:
    """El producto debe mencionar 'triciclo' en la URL o en su título."""
    return TERMINO_BUSQUEDA in url.lower() or TERMINO_BUSQUEDA in (texto or "").lower()


def descubrir_urls(sesion: requests.Session, pausa: float, paginas_busqueda: int) -> tuple[list[str], list[str]]:
    """
    Recorre categoría y búsqueda para reunir las URLs de los triciclos.
    Devuelve (urls, urls_visitadas).
    """
    candidatas: list[str] = []
    visitadas: list[str] = []

    for url_categoria in URLS_CATEGORIA:
        visitadas.append(url_categoria)
        html = descargar(sesion, url_categoria, pausa)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        enlaces = enlaces_producto(soup, url_categoria)
        tricyclos = [url for url, texto in enlaces if es_triciclo(url, texto)]
        log(f"categoría {url_categoria} -> {len(enlaces)} enlaces, {len(tricyclos)} triciclos")
        if tricyclos:
            for url in tricyclos:
                if url not in candidatas:
                    candidatas.append(url)
            break  # la primera categoría válida es suficiente
        time.sleep(pausa)

    for pagina in range(1, max(1, paginas_busqueda) + 1):
        url_busqueda = URL_BUSQUEDA if pagina == 1 else f"{SITIO}/page/{pagina}/?s={TERMINO_BUSQUEDA}&post_type=product"
        visitadas.append(url_busqueda)
        html = descargar(sesion, url_busqueda, pausa)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for url, texto in enlaces_producto(soup, url_busqueda):
            if es_triciclo(url, texto) and url not in candidatas:
                candidatas.append(url)
        log(f"búsqueda página {pagina} -> {len(candidatas)} triciclos acumulados")
        time.sleep(pausa)

    return candidatas, visitadas


# ---------------------------------------------------------------------------
# Extracción de la ficha
# ---------------------------------------------------------------------------


def json_ld_grafo(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Todos los nodos JSON-LD de la página."""
    nodos: list[dict[str, Any]] = []
    for etiqueta in soup.find_all("script", type="application/ld+json"):
        try:
            datos = json.loads(etiqueta.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(datos, dict):
            grafo = datos.get("@graph")
            nodos.extend(n for n in grafo if isinstance(n, dict)) if isinstance(grafo, list) else nodos.append(datos)
        elif isinstance(datos, list):
            nodos.extend(n for n in datos if isinstance(n, dict))
    return nodos


def json_ld_producto(soup: BeautifulSoup) -> dict[str, Any]:
    """Nodo Product del JSON-LD de la ficha (vacío si no existe)."""
    for nodo in json_ld_grafo(soup):
        if nodo.get("@type") == "Product":
            return nodo
    return {}


def id_post(body_class: list[str]) -> str:
    for clase in body_class:
        if clase.startswith("postid-"):
            return clase[len("postid-"):]
    return ""


def clases_producto(soup: BeautifulSoup) -> list[str]:
    """
    Clases del contenedor del producto (WooCommerce). ahí viven 'outofstock',
    'instock' y 'preorder'; el <body> no las lleva.
    """
    for selector in ("article.single-product-page", ".single-product-page", ".product.type-product"):
        elemento = soup.select_one(selector)
        if elemento:
            clases = elemento.get("class") or []
            return list(clases) if not isinstance(clases, str) else clases.split()
    return []


def texto_disponibilidad(soup: BeautifulSoup) -> str:
    for selector in (".wd-single-stock-status", ".wd_single_stock_status", ".stock"):
        for elemento in soup.select(selector):
            texto = normalizar_espacios(elemento.get_text(" ", strip=True))
            if texto:
                return texto
    return ""


def disponibilidad_canonica(json_ld: dict[str, Any], clases: list[str], texto_stock: str) -> str:
    """Normaliza la disponibilidad a: in_stock | out_of_stock | preorder | unknown."""
    url_oferta = ""
    ofertas = json_ld.get("offers") or []
    if isinstance(ofertas, dict):
        ofertas = [ofertas]
    if ofertas and isinstance(ofertas[0], dict):
        url_oferta = str(ofertas[0].get("availability") or "")

    if "outofstock" in url_oferta.lower() or "outofstock" in clases:
        return "out_of_stock"
    if "instock" in url_oferta.lower() or "instock" in clases:
        return "in_stock"
    if "preorder" in url_oferta.lower() or "preorder" in clases:
        return "preorder"
    if texto_stock:
        bajo = texto_stock.lower()
        if "existencias" in bajo or "agotado" in bajo or "sin stock" in bajo:
            return "out_of_stock"
        if "disponible" in bajo:
            return "in_stock"
    return "unknown"


def extraer_ofertas(json_ld: dict[str, Any]) -> tuple[float | None, str]:
    """Precio base (menor oferta) y moneda del JSON-LD."""
    ofertas = json_ld.get("offers") or []
    if isinstance(ofertas, dict):
        ofertas = [ofertas]
    precios: list[float] = []
    moneda = ""
    for oferta in ofertas:
        if not isinstance(oferta, dict):
            continue
        moneda = str(oferta.get("priceCurrency") or moneda)
        specs = oferta.get("priceSpecification") or []
        if isinstance(specs, dict):
            specs = [specs]
        candidatos = [oferta.get("price")] + [s.get("price") for s in specs if isinstance(s, dict)]
        for candidato in candidatos:
            valor = a_numero(str(candidato)) if candidato is not None else None
            if valor:
                precios.append(valor)
    precio = min(precios) if precios else None
    return precio, moneda


def precio_desde_html(soup: BeautifulSoup) -> tuple[float | None, str, bool]:
    """
    Respaldo: precio del widget principal de la ficha (no de productos
    relacionados). El segundo valor es el texto; el tercero indica si hay
    precio original tachado (<del>), es decir, si está en oferta.
    """
    for selector in (".wd-single-price", ".elementor-widget-wd_single_product_price"):
        for elemento in soup.select(selector):
            texto = normalizar_espacios(elemento.get_text(" ", strip=True))
            precio = a_numero(texto)
            if precio:
                return precio, texto, elemento.find("del") is not None
    return None, "", False


def texto_especificacion(elemento: Any) -> str:
    """
    Texto de un <li> de especificaciones, cortado en el primer <br> (las notas
    entre paréntesis no son parte del valor).

    El editor del sitio parte algunos valores dentro del <strong>
    ('<strong>Potencia del motor: 3</strong>000W'), por eso se pegan los
    números que quedaron separados por un espacio.
    """
    partes: list[str] = []
    for hijo in elemento.children:
        if getattr(hijo, "name", None) == "br":
            break
        if isinstance(hijo, NavigableString):
            partes.append(str(hijo))
        else:
            partes.append(hijo.get_text(" ", strip=True))
    texto = normalizar_espacios(" ".join(partes))
    return re.sub(r"(?<=\d)\s+(?=\d)", "", texto)


def parsear_especificaciones(soup: BeautifulSoup) -> tuple[list[dict[str, str]], list[str]]:
    """
    Extrae las especificaciones de la ficha.

    El sitio usa dos formatos:
      A) <p>Sección</p><ul><li><strong>Etiqueta:</strong> Valor</li></ul>
      B) <ul><li>Etiqueta: Valor</li></ul>
    En ambos el par etiqueta/valor se separa por el primer ':'. Los <li> sin
    ':' son características, no especificaciones.
    """
    contenedor = None
    for selector in (
        ".wd_single_product_content",
        ".elementor-widget-wd_single_product_content",
        ".wd-single-content",
        ".woocommerce-product-details",
    ):
        encontrado = soup.select_one(selector)
        if encontrado:
            contenedor = encontrado
            break
    if contenedor is None:
        return [], []

    especificaciones: list[dict[str, str]] = []
    caracteristicas: list[str] = []

    for elemento in contenedor.find_all(["li", "p"]):
        if elemento.name == "p":
            continue  # encabezado de sección
        texto_completo = normalizar_espacios(elemento.get_text(" ", strip=True))
        if not texto_completo:
            continue

        texto = texto_especificacion(elemento)
        if ":" in texto:
            etiqueta, valor = texto.split(":", 1)
            etiqueta = normalizar_espacios(etiqueta)
            valor = normalizar_espacios(valor)
            if etiqueta and valor:
                especificaciones.append(
                    {"etiqueta": etiqueta, "valor": valor, "texto_completo": texto_completo}
                )
                continue
        caracteristicas.append(texto_completo)

    return especificaciones, caracteristicas


def buscar_valor(especificaciones: list[dict[str, str]], etiquetas: tuple[str, ...]) -> str:
    """Busca el valor de una especificación por etiqueta (sin distinguir acentos)."""
    claves = [sin_acentos(clave) for clave in etiquetas]
    for clave in claves:
        for especificacion in especificaciones:
            if sin_acentos(especificacion["etiqueta"]) == clave:
                return especificacion["valor"]
    for clave in claves:
        for especificacion in especificaciones:
            if clave in sin_acentos(especificacion["etiqueta"]):
                return especificacion["valor"]
    return ""


def derivar_marca(titulo: str, sku: str, nombre_importadora: str) -> str:
    """Marca: la del titular del catálogo (este sitio no usa taxonomía de marcas)."""
    if nombre_importadora and nombre_importadora.lower() in titulo.lower():
        return nombre_importadora
    coincidencia = re.match(r"^([A-Za-z0-9\-]{2,6})-", sku or "")
    if coincidencia:
        return coincidencia.group(1)
    return ""


def derivar_modelo(titulo: str, sku: str, nombre_importadora: str) -> str:
    """
    Modelo comercial: el título sin tipo de propulsión, tokens técnicos ni marca.
    Si no queda nada, se recurre al SKU (prefijo de marca y línea eliminados).
    """
    texto = titulo
    if nombre_importadora:
        texto = re.sub(re.escape(nombre_importadora), " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\btriciclos?\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bde\b|\bcon\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bel[ée]ctric[oa]?\b|\bcombusti[oó]n\b|\bcombustion\b", " ", texto, flags=re.IGNORECASE)
    texto = RE_TOKEN_TECNICO_COMPUESTO.sub(" ", texto)
    texto = RE_TOKEN_TECNICO.sub(" ", texto)
    texto = re.sub(r"[/(),]+", " ", texto)
    texto = normalizar_espacios(texto)

    if texto:
        return texto.upper()

    # Respaldo: SKU sin el prefijo de marca/línea (p. ej. 'MZ-TRC 250 C-RUNNER').
    limpio_sku = re.sub(r"^[A-Za-z0-9]{2,6}-(?:[A-Za-z0-9]{2,6}-)?", " ", sku or "")
    limpio_sku = RE_TOKEN_TECNICO_COMPUESTO.sub(" ", limpio_sku)
    limpio_sku = RE_TOKEN_TECNICO.sub(" ", limpio_sku)
    limpio_sku = re.sub(r"\b\d+\b", " ", limpio_sku)
    limpio_sku = normalizar_espacios(limpio_sku)
    if limpio_sku:
        return limpio_sku.upper()
    return (titulo or sku or "").strip().upper()


def derivar_tipo(titulo: str, especificaciones: list[dict[str, str]]) -> str:
    valor = buscar_valor(especificaciones, ETIQUETAS_TIPO)
    texto = f"{titulo} {valor}"
    if RE_TIPO_COMBUSTION.search(texto):
        return "combustion"
    if RE_TIPO_ELECTRICO.search(texto):
        return "electric"
    return ""


def extraer_ficha(sesion: requests.Session, url: str, pausa: float) -> dict[str, Any]:
    """Descarga y extrae una ficha de producto."""
    html = descargar(sesion, url, pausa)
    if html is None:
        raise RuntimeError(f"no se pudo descargar {url}")

    soup = BeautifulSoup(html, "html.parser")
    json_ld = json_ld_producto(soup)
    body = soup.find("body")
    body_class = body.get("class") if body else []
    if isinstance(body_class, str):
        body_class = body_class.split()
    clases_prod = clases_producto(soup)

    titulo = normalizar_espacios((json_ld.get("name") or "")) or normalizar_espacios(
        (soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")
    )
    sku = normalizar_espacios(str(json_ld.get("sku") or ""))

    vendedor = json_ld.get("seller") or {}
    nombre_importadora = (
        normalizar_espacios(str(vendedor.get("name") or ""))
        if isinstance(vendedor, dict)
        else ""
    ) or NOMBRE_IMPORTADORA

    precio, moneda = extraer_ofertas(json_ld)
    texto_precio = ""
    en_oferta = False
    if precio is None:
        precio, texto_precio, en_oferta = precio_desde_html(soup)
    if not texto_precio:
        for elemento in soup.select(".wd-single-price"):
            texto_precio = normalizar_espacios(elemento.get_text(" ", strip=True))
            en_oferta = en_oferta or elemento.find("del") is not None
            break

    especificaciones, caracteristicas = parsear_especificaciones(soup)
    texto_stock = texto_disponibilidad(soup)
    if not texto_stock:
        # WooCommerce renderiza la etiqueta de stock por JS; se usa la que
        # corresponde a la clase del contenedor (mismo texto que muestra el sitio).
        if "outofstock" in clases_prod:
            texto_stock = "Sin existencias"
        elif "instock" in clases_prod:
            texto_stock = "Disponible"
    descripcion_corta = ""
    for selector in (".woocommerce-product-details__short-description", ".wd-single-short-description"):
        elemento = soup.select_one(selector)
        if elemento:
            descripcion_corta = normalizar_espacios(elemento.get_text(" ", strip=True))
            break

    categorias = []
    for nodo in json_ld_grafo(soup):
        if nodo.get("@type") != "BreadcrumbList":
            continue
        for item in (nodo.get("itemListElement") or []):
            if not isinstance(item, dict):
                continue
            # El nombre puede venir en el ListItem o anidado en 'item'.
            origen = item.get("item") if isinstance(item.get("item"), dict) else item
            nombre = normalizar_espacios(str(origen.get("name") or ""))
            if not nombre or sin_acentos(nombre) in ("inicio", "home"):
                continue
            # El último peldaño del breadcrumb es el propio producto, no una categoría.
            if sin_acentos(nombre) == sin_acentos(titulo):
                continue
            categorias.append(nombre)
        break

    texto_tecnico = " ".join(
        [titulo, descripcion_corta]
        + [f"{e['etiqueta']} {e['valor']}" for e in especificaciones]
        + caracteristicas
    )

    autonomia = a_rango_numerico(buscar_valor(especificaciones, ETIQUETAS_AUTONOMIA))
    voltaje = a_rango_numerico(buscar_valor(especificaciones, ETIQUETAS_VOLTAJE))
    capacidad_carga = a_rango_numerico(buscar_valor(especificaciones, ETIQUETAS_CARGA))
    if voltaje:
        voltaje = voltaje.split("-")[0]  # "72V / 100Ah" -> voltaje 72

    return {
        "id": id_post(body_class),
        "url": url,
        "titulo": titulo,
        "sku": sku,
        "nombre_importadora": nombre_importadora,
        "marca": derivar_marca(titulo, sku, nombre_importadora),
        "modelo": derivar_modelo(titulo, sku, nombre_importadora),
        "tipo": derivar_tipo(titulo, especificaciones),
        "precio_usd": precio,
        "moneda": moneda or "USD",
        "texto_precio": texto_precio,
        "precio_en_oferta": en_oferta,
        "tiene_panel_solar": bool(RE_PANEL_SOLAR.search(texto_tecnico)),
        "capacidad_carga_kg": capacidad_carga,
        "autonomia_km": autonomia,
        "voltaje_bateria": voltaje,
        "disponibilidad": disponibilidad_canonica(json_ld, clases_prod, texto_stock),
        "texto_disponibilidad": texto_stock,
        "categorias": categorias,
        "descripcion_corta": descripcion_corta,
        "especificaciones": especificaciones,
        "caracteristicas": caracteristicas,
        "fecha_scraping": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Escritura de salidas
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
            "script": "scraping/catalogos/scraper_mzproducts.py",
            "fecha_scraping": date.today().isoformat(),
            "urls_visitadas": visitadas,
            "n_urls_visitadas": len(visitadas),
            "n_productos": len(fichas),
            "n_errores": len(errores),
            "errores": errores,
            "nota": "Precios en USD tal como los publica el vendedor (importación a Cuba).",
        },
        "productos": fichas,
    }
    ARCHIVO_CRUDO.write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8"
    )
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
# Programa
# ---------------------------------------------------------------------------


def main() -> int:
    global TIMEOUT

    analizador = argparse.ArgumentParser(description="Scraper de triciclos en MZ Products")
    analizador.add_argument("--solo", metavar="URL", help="extrae una única ficha de producto")
    analizador.add_argument("--paginas", type=int, default=2, help="páginas de búsqueda a recorrer")
    analizador.add_argument("--pausa", type=float, default=3.0, help="pausa entre peticiones (s)")
    analizador.add_argument("--timeout", type=int, default=TIMEOUT, help="timeout HTTP (s)")
    argumentos = analizador.parse_args()

    TIMEOUT = argumentos.timeout

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
        except Exception as exc:  # noqa: BLE001 - se reporta y sigue
            log(f"ERROR en {url}: {exc}")
            errores.append({"url": url, "error": str(exc)})
    else:
        urls, visitadas = descubrir_urls(sesion, argumentos.pausa, argumentos.paginas)
        log(f"{len(urls)} triciclos detectados")
        for indice, url in enumerate(urls, start=1):
            try:
                ficha = extraer_ficha(sesion, url, argumentos.pausa)
                fichas.append(ficha)
                log(
                    f"[{indice}/{len(urls)}] {ficha['modelo'] or ficha['titulo']} | "
                    f"{ficha['precio_usd']} USD | {ficha['disponibilidad']}"
                )
            except Exception as exc:  # noqa: BLE001 - se reporta y sigue
                log(f"ERROR en {url}: {exc}")
                errores.append({"url": url, "error": str(exc)})
            time.sleep(argumentos.pausa)

    escribir_crudo(fichas, visitadas, errores)
    escribir_csv(fichas)

    log(f"fin: {len(fichas)} fichas, {len(errores)} errores")
    return 1 if errores and not fichas else 0


if __name__ == "__main__":
    sys.exit(main())
